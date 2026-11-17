# C1 BLE protocol notes

Observed on firmware 1.00.09. Standalone transport physically validated on macOS;
this integration has not been printed from. No private captures are distributed.

- ISSC service: `49535343-fe7d-4ae5-8fa9-9fafd205e455`.
- Control write: `49535343-6daa-4d02-abf6-19569aca69fe` (with response).
- Bitmap fast write: `49535343-8841-43f4-a8d4-ecbe34729bb3` (without response).
- Notify: `49535343-1e4d-4bd9-ba61-23c647249616`.
- Frame: `02 | cmd:u8 | sequence:u8 | length:u16LE | payload | crc:u32LE | 03`.
- CRC is `zlib.crc32(payload)` with seed zero, unlike older P1/P2 implementations.
- Query payload is `01`, sequence zero. Expect command+1 data and command ACK `00`.
- Model-query fixture: TX `0206000100011bdf05a503`, RX
  `02070002004331030e53cb03` and `0206000100008def02d203`.
- Bitmap command `00`: 1248 dots, 156 bytes/row, black=1, MSB first.
  Send up to six rows per packet (936 bytes). Fast fragments <=117 bytes and
  negotiated write limit, 10 ms pause, status barrier after four packets and last.
- Feed `1A`: uint16LE rows. Control commands retain response writes.
- Status `0000` is the observed ready state; other bits are not decoded.
- No bitmap ACK assumption, no automatic retry or parameter initialization writes.

An equal 140-row standalone test took 20.699 s in normal mode and 4.829 s in fast
mode through feed ACK, excluding connection. The user confirmed intact text and
borders; this is not a measurement of motor speed or an integrated-driver claim.

Protocol references: [paperang-web](https://github.com/Yrr0r/paperang-web),
[miaomiaoji-tool](https://github.com/ihciah/miaomiaoji-tool),
[paperang-p2-lib](https://github.com/mdj2812/paperang-p2-lib).
C1 code is independently implemented from protocol observations.
