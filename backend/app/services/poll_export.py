"""Poll results CSV export service."""

import csv
import io
import logging

from app.models.poll import Poll

logger = logging.getLogger(__name__)

# Leading chars a spreadsheet treats as the start of a formula (CWE-1236).
_CSV_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _neutralize_csv(value: object) -> object:
    """Defang spreadsheet formula injection in a user-controlled CSV cell.

    csv.writer quotes structure but does NOT neutralize formulas: a cell whose
    first char is = + - @ TAB or CR is executed when the file is opened in
    Excel/Sheets. Prefix such strings with a single quote so they render as
    text. Non-strings pass through unchanged.
    """
    if isinstance(value, str) and value.startswith(_CSV_FORMULA_PREFIXES):
        return "'" + value
    return value


def generate_poll_csv(poll: Poll) -> str:
    """Generate CSV content for poll results.

    Returns CSV as a string with columns:
    Option, Votes, Percentage
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header (poll title/description are user-controlled — neutralize formulas)
    writer.writerow(["Poll", _neutralize_csv(poll.title)])
    if poll.description:
        writer.writerow(["Description", _neutralize_csv(poll.description)])
    writer.writerow(["Status", "Closed" if poll.is_closed else "Open"])

    unique_voters = {v.user_id for v in poll.votes}
    writer.writerow(["Total Voters", str(len(unique_voters))])
    writer.writerow([])  # Blank row

    # Results header
    writer.writerow(["Option", "Votes", "Percentage"])

    total_option_votes = sum(
        len([v for v in poll.votes if v.option_id == opt.id]) for opt in poll.options
    )

    for opt in sorted(poll.options, key=lambda o: o.display_order):
        vote_count = len([v for v in poll.votes if v.option_id == opt.id])
        pct = round((vote_count / total_option_votes * 100), 1) if total_option_votes > 0 else 0.0
        writer.writerow([_neutralize_csv(opt.text), str(vote_count), f"{pct}%"])

    return output.getvalue()
