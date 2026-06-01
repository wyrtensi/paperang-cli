"""Model-specific public API facades for paperang-cli."""

from paperang_cli.api.contract import (
	API_CONTRACTS,
	P1_API_CONTRACT,
	P2_API_CONTRACT,
	format_api_catalog_human_lines,
	format_api_contract_human_lines,
	format_p1_api_contract_human_lines,
	get_api_contract,
	list_api_contract_summaries,
)
from paperang_cli.api.p1 import PaperangP1
from paperang_cli.api.p2 import PaperangP2

__all__ = [
	"API_CONTRACTS",
	"P1_API_CONTRACT",
	"P2_API_CONTRACT",
	"PaperangP1",
	"PaperangP2",
	"format_api_catalog_human_lines",
	"format_api_contract_human_lines",
	"format_p1_api_contract_human_lines",
	"get_api_contract",
	"list_api_contract_summaries",
]