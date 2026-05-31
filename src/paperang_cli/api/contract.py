"""Read-only contract data for the public Paperang Python API facades."""

from __future__ import annotations


P1_API_CONTRACT = {
    "api": "p1",
    "availability": {
        "available": True,
        "status": "available",
        "note": "Supported in this package version.",
    },
    "class_name": "PaperangP1",
    "import_path": "from paperang_cli import PaperangP1",
    "implementation_module": "paperang_cli.api.p1",
    "model": "paperang_p1",
    "transport": "ble",
    "config_loading": {
        "default_behavior": "The constructor uses built-in defaults unless config_path is provided. A config file can also provide nested print_defaults for text, paragraph, image, and compose styling.",
        "config_path_supported": True,
    },
    "constructor_options": [
        {
            "name": "address",
            "type": "str | None",
            "default": None,
            "description": "Optional BLE MAC address override.",
        },
        {
            "name": "config_path",
            "type": "str | os.PathLike[str] | None",
            "default": None,
            "description": "Optional path to a paperang-cli JSON config file.",
        },
        {
            "name": "printer_width",
            "type": "int | None",
            "default": None,
            "description": "Optional override for the printer render width.",
        },
        {
            "name": "print_density",
            "type": "int | None",
            "default": None,
            "description": "Optional override for the configured heat density.",
        },
        {
            "name": "post_print_feed_mm",
            "type": "float | None",
            "default": None,
            "description": "Optional override for the calibrated post-print feed.",
        },
        {
            "name": "discovery_names",
            "type": "list[str] | None",
            "default": None,
            "description": "Optional list of BLE advertising names to scan for.",
        },
    ],
    "methods": [
        {
            "name": "discover",
            "returns": "list[PrinterDevice]",
            "paper_consuming": False,
            "description": "Discover nearby supported Paperang BLE devices.",
        },
        {
            "name": "connect",
            "returns": "PaperangP1",
            "paper_consuming": False,
            "description": "Run a non-printing readiness check and cache the resolved address for follow-up calls.",
        },
        {
            "name": "disconnect",
            "returns": "None",
            "paper_consuming": False,
            "description": "Clear the cached address used by the facade.",
        },
        {
            "name": "get_status",
            "returns": "PrinterStatus",
            "paper_consuming": False,
            "description": "Query live printer status without printing.",
        },
        {
            "name": "get_battery",
            "returns": "BatteryStatus",
            "paper_consuming": False,
            "description": "Query battery percentage without printing.",
        },
        {
            "name": "get_bluetooth_mac",
            "returns": "BluetoothMacStatus",
            "paper_consuming": False,
            "description": "Query the printer-reported Bluetooth MAC address.",
        },
        {
            "name": "get_bt_mac",
            "returns": "BluetoothMacStatus",
            "paper_consuming": False,
            "description": "Compatibility alias for get_bluetooth_mac().",
        },
        {
            "name": "print_text",
            "returns": "PrintResult",
            "paper_consuming": True,
            "description": "Print a short text block using the existing text rendering path, with optional font family, rotated orientation, and rotated-label autofit.",
        },
        {
            "name": "print_paragraph",
            "returns": "PrintResult",
            "paper_consuming": True,
            "description": "Print wrapped text using the paragraph rendering path, with optional font family, rotated orientation, and rotated-label autofit.",
        },
        {
            "name": "print_image",
            "returns": "PrintResult",
            "paper_consuming": True,
            "description": "Print a local image with mode or conversion normalization delegated to the current render layer, including optional 90-degree orientation.",
        },
        {
            "name": "print_compose",
            "returns": "PrintResult",
            "paper_consuming": True,
            "description": "Print wrapped text plus a local image in one composed job.",
        },
        {
            "name": "print_self_test",
            "returns": "PrintResult",
            "paper_consuming": True,
            "description": "Run the printer self-test with the existing large-paper safety gate.",
        },
    ],
    "safety": {
        "allow_paper_use_methods": [
            "print_text",
            "print_paragraph",
            "print_image",
            "print_compose",
        ],
        "allow_large_paper_use_methods": ["print_self_test"],
        "dry_run_methods": [
            "print_text",
            "print_paragraph",
            "print_image",
            "print_compose",
            "print_self_test",
        ],
        "notes": [
            "Real printing still flows through the existing driver and safety checks.",
            "Dry-run results now include a styling object that reports the resolved render options used for the job.",
            "Image and compose printing remain experimental until validated on real hardware.",
        ],
    },
    "styling_support": {
        "config_defaults": "Nested print_defaults values can define default styling for text, paragraph, image, and compose jobs.",
        "generic_font_families": ["sans", "mono", "serif"],
        "orientations": ["normal", "rotate-90-cw", "rotate-90-ccw"],
        "rotated_methods": ["print_text", "print_paragraph", "print_image"],
        "rotated_compose_supported": False,
        "print_result_field": "PrintResult.styling",
    },
    "unsupported_parity_gaps": [
        "USB, cable, and local data transports are not supported for Paperang P1 in this project.",
        "P2-only features such as QR printing, pickup-code printing, and print profiles are not implemented.",
        "Rotated compose printing is not implemented yet; compose remains an ordinary vertical layout in this release.",
        "The public Python API intentionally does not expose a stable low-level packet or transport contract.",
    ],
}

P2_API_CONTRACT = {
    "api": "p2",
    "availability": {
        "available": False,
        "status": "coming-soon",
        "note": "Reserved placeholder for a future P2-specific facade. No public Python API, driver, or print path is available yet.",
    },
    "class_name": None,
    "planned_class_name": "PaperangP2",
    "import_path": None,
    "implementation_module": None,
    "model": "paperang_p2",
    "transport": None,
    "config_loading": {
        "default_behavior": "Unavailable until the P2 facade and driver are implemented.",
        "config_path_supported": False,
    },
    "constructor_options": [],
    "methods": [],
    "safety": {
        "allow_paper_use_methods": [],
        "allow_large_paper_use_methods": [],
        "dry_run_methods": [],
        "notes": [
            "No public print or query methods are available for P2 in this package version.",
        ],
    },
    "unsupported_parity_gaps": [
        "No P2 driver is registered in this project yet.",
        "No public PaperangP2 facade is exported yet.",
        "No CLI print, query, or transport support exists for P2 yet.",
    ],
}

API_CONTRACTS = {
    "p1": P1_API_CONTRACT,
    "p2": P2_API_CONTRACT,
}


def get_api_contract(api_name: str) -> dict:
    """Return the public contract for a model-specific API placeholder or facade."""

    return API_CONTRACTS[api_name]


def list_api_contract_summaries() -> list[dict[str, object]]:
    """Return concise summaries for all known model-specific API entries."""

    summaries = []
    for api_name, contract in API_CONTRACTS.items():
        summaries.append(
            {
                "api": api_name,
                "model": contract["model"],
                "available": contract["availability"]["available"],
                "status": contract["availability"]["status"],
                "class_name": contract.get("class_name"),
                "planned_class_name": contract.get("planned_class_name"),
            }
        )

    return summaries


def format_api_contract_human_lines(api_name: str) -> list[str]:
    """Return a human-readable summary of a public model-specific API contract."""

    contract = get_api_contract(api_name)
    lines = [
        f"API: {contract['class_name'] or contract.get('planned_class_name') or contract['api']}",
        f"Status: {contract['availability']['status']}",
        f"Availability note: {contract['availability']['note']}",
        f"Model: {contract['model']}",
        f"Transport: {contract['transport']}",
    ]

    if contract.get("import_path"):
        lines.append(f"Import: {contract['import_path']}")
    else:
        lines.append("Import: unavailable in this package version")

    if contract.get("implementation_module"):
        lines.append(f"Implementation module: {contract['implementation_module']}")
    else:
        lines.append("Implementation module: unavailable")

    lines.append(f"Config loading: {contract['config_loading']['default_behavior']}")
    if contract.get("styling_support"):
        styling = contract["styling_support"]
        lines.append("Styling support:")
        lines.append(f"- Config defaults: {styling['config_defaults']}")
        lines.append(f"- Font families: {', '.join(styling['generic_font_families'])}")
        lines.append(f"- Orientations: {', '.join(styling['orientations'])}")
        lines.append(f"- Rotated methods: {', '.join(styling['rotated_methods'])}")
        lines.append(f"- Rotated compose supported: {styling['rotated_compose_supported']}")
        lines.append(f"- Resolved styling field: {styling['print_result_field']}")
    lines.append("Constructor options:")
    for option in contract["constructor_options"]:
        lines.append(
            f"- {option['name']} ({option['type']}, default={option['default']}): {option['description']}"
        )

    if not contract["constructor_options"]:
        lines.append("- unavailable")

    lines.append("Methods:")
    for method in contract["methods"]:
        safety_note = "paper-consuming" if method["paper_consuming"] else "non-printing"
        lines.append(f"- {method['name']}() -> {method['returns']} [{safety_note}]")

    if not contract["methods"]:
        lines.append("- unavailable")

    lines.append("Safety:")
    if contract["safety"]["allow_paper_use_methods"]:
        lines.append(
            "- allow_paper_use required for: " + ", ".join(contract["safety"]["allow_paper_use_methods"])
        )
    if contract["safety"]["allow_large_paper_use_methods"]:
        lines.append(
            "- allow_large_paper_use required for: "
            + ", ".join(contract["safety"]["allow_large_paper_use_methods"])
        )
    for note in contract["safety"]["notes"]:
        lines.append(f"- {note}")

    lines.append("Unsupported parity gaps:")
    for note in contract["unsupported_parity_gaps"]:
        lines.append(f"- {note}")

    return lines


def format_p1_api_contract_human_lines() -> list[str]:
    """Return a human-readable summary of the public P1 API contract."""

    return format_api_contract_human_lines("p1")


def format_api_catalog_human_lines() -> list[str]:
    """Return a human-readable summary of all known API entries."""

    lines = ["Known model-specific APIs:"]
    for item in list_api_contract_summaries():
        label = item["class_name"] or item["planned_class_name"] or item["api"]
        lines.append(f"- {item['api']}: {item['status']} ({label})")

    return lines