from paperang_cli.protocol.p2_ble_ff00 import (
    A5_START_RASTER_PAYLOAD,
    A5_MAX_FRAME_SIZE,
    a5_feed_rows_from_units,
    a5_print_chunk_size,
    build_a5_finish_payload,
    build_a5_payload,
    build_a5_print_data_payload,
    first_a5_text_value,
    is_a5_success_response,
    parse_a5_frame,
    parse_a5_payload,
    parse_a5_tlv_args,
    pack_a5_frame,
)


def test_pack_a5_frame_uses_seeded_crc32():
    packet = pack_a5_frame(A5_START_RASTER_PAYLOAD)

    assert packet.hex() == "a5010500051901000039cb63a65a"


def test_parse_a5_frame_validates_crc_and_payload():
    packet = bytes.fromhex("a50108000519020300010000855bb8e85a")

    frame = parse_a5_frame(packet)

    assert frame is not None
    assert frame.payload == bytes.fromhex("0519020300010000")
    assert frame.crc == 0xE8B85B85


def test_build_a5_payload_uses_domain_command_kind_and_arg_length():
    payload = build_a5_payload(0x05, 0x11, bytes([0x40]))

    assert payload == bytes.fromhex("051101010040")


def test_build_rawbt_style_print_data_payload():
    payload = build_a5_print_data_payload(bytes([0xFF]) * 72, chunk_number=1, width_bytes=72, final=True)

    assert payload[:17] == bytes.fromhex("051b035400010050000148000000004800")
    assert payload[17:] == bytes([0xFF]) * 72


def test_build_finish_payload_matches_rawbt_driver():
    assert build_a5_finish_payload() == bytes.fromhex("05220102000000")


def test_print_chunk_size_is_row_aligned_for_windows_ble_limit():
    assert a5_print_chunk_size(72) == 144
    assert a5_print_chunk_size(48) == 192


def test_p2_print_chunk_frame_fits_ble_write_limit():
    data = bytes([0xFF]) * a5_print_chunk_size(72)
    frame = pack_a5_frame(build_a5_print_data_payload(data, chunk_number=1, width_bytes=72, final=False))

    assert len(frame) <= A5_MAX_FRAME_SIZE


def test_feed_rows_from_cli_units_uses_approximate_p2_dot_pitch():
    assert a5_feed_rows_from_units(0) == 0
    assert a5_feed_rows_from_units(280) == 40


def test_parse_a5_payload_extracts_inner_command_fields():
    command = parse_a5_payload(bytes.fromhex("0115020b0001080030312e30332e3039"))

    assert command is not None
    assert command.domain == 0x01
    assert command.command == 0x15
    assert command.kind == 0x02
    assert command.args == bytes.fromhex("01080030312e30332e3039")


def test_parse_a5_tlv_args_extracts_values():
    values = parse_a5_tlv_args(bytes.fromhex("01080030312e30332e3039"))

    assert values == {0x01: bytes.fromhex("30312e30332e3039")}
    assert first_a5_text_value(bytes.fromhex("01080030312e30332e3039")) == "01.03.09"


def test_is_a5_success_response_accepts_ack_tlv():
    response = parse_a5_payload(bytes.fromhex("0511020300010000"))

    assert response is not None
    assert is_a5_success_response(response)


def test_parse_a5_frame_rejects_non_a5_packet():
    assert parse_a5_frame(bytes.fromhex("0101")) is None


def test_parse_a5_frame_rejects_bad_crc():
    packet = bytearray(bytes.fromhex("a50108000519020300010000855bb8e85a"))
    packet[-2] ^= 0x01

    assert parse_a5_frame(bytes(packet)) is None
