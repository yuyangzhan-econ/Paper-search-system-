"""
Journal Abbreviation Mapping
Maps common abbreviations to full journal names for search.
Focus on economics, political science, and finance top journals.
"""

# Mapping of abbreviation -> list of possible full names (from CrossRef)
JOURNAL_ABBREVIATIONS = {
    # Economics Top 5
    'AER': ['American Economic Review', 'The American Economic Review', 'Am Econ Rev'],
    'QJE': ['Quarterly Journal of Economics', 'The Quarterly Journal of Economics', 'Q J Econ'],
    'JPE': ['Journal of Political Economy', 'J Polit Econ', 'J Political Economy'],
    'ECMA': ['Econometrica', 'Econometrica Journal of the Econometric Society'],
    'RES': ['Review of Economic Studies', 'The Review of Economic Studies', 'Rev Econ Stud'],

    # Political Science
    'APSR': ['American Political Science Review', 'Am Polit Sci Rev'],
    'AJPS': ['American Journal of Political Science', 'Am J Polit Sci'],
    'JOP': ['Journal of Politics', 'The Journal of Politics', 'J Polit'],

    # Other Top Economics Journals
    'JPubE': ['Journal of Public Economics', 'J Public Econ'],
    'EJ': ['Economic Journal', 'The Economic Journal', 'Econ J'],
    'JEEA': ['Journal of the European Economic Association', 'J Eur Econ Assoc'],
    'REStat': ['Review of Economics and Statistics', 'The Review of Economics and Statistics', 'Rev Econ Stat'],
    'JLE': ['Journal of Law and Economics', 'J Law Econ'],
    'JDE': ['Journal of Development Economics', 'J Dev Econ'],
    'JHE': ['Journal of Health Economics', 'J Health Econ'],
    'JUE': ['Journal of Urban Economics', 'J Urban Econ'],
    'JME': ['Journal of Monetary Economics', 'J Monet Econ'],
    'JIE': ['Journal of International Economics', 'J Int Econ'],
    'JEG': ['Journal of Economic Growth', 'J Econ Growth'],
    'JOLE': ['Journal of Labor Economics', 'J Labor Econ'],
    'RAND': ['RAND Journal of Economics', 'The RAND Journal of Economics'],
    'ReStud': ['Review of Economic Studies', 'The Review of Economic Studies'],
    'AEJ': ['American Economic Journal', 'AEJ: Applied Economics', 'AEJ: Economic Policy', 'AEJ: Macroeconomics', 'AEJ: Microeconomics'],
    'AEJApp': ['American Economic Journal: Applied Economics', 'AEJ: Applied Economics'],
    'AEJPol': ['American Economic Journal: Economic Policy', 'AEJ: Economic Policy'],
    'AEJMacro': ['American Economic Journal: Macroeconomics', 'AEJ: Macroeconomics'],
    'AEJMicro': ['American Economic Journal: Microeconomics', 'AEJ: Microeconomics'],

    # Finance
    'JFE': ['Journal of Financial Economics', 'J Financ Econ'],
    'RFS': ['Review of Financial Studies', 'The Review of Financial Studies', 'Rev Financ Stud'],
    'JoF': ['Journal of Finance', 'The Journal of Finance', 'J Finance'],
    'JF': ['Journal of Finance', 'The Journal of Finance', 'J Finance'],
    'JFI': ['Journal of Financial Intermediation', 'J Financ Intermed'],
    'JFQA': ['Journal of Financial and Quantitative Analysis', 'J Financ Quant Anal'],

    # Game Theory / Theory
    'GEB': ['Games and Economic Behavior', 'Game Econ Behav'],
    'ET': ['Economic Theory', 'Econ Theory'],
    'JET': ['Journal of Economic Theory', 'J Econ Theory'],
    'TE': ['Theoretical Economics'],
    'AER:I': ['AER: Insights', 'American Economic Review: Insights'],

    # Other
    'NBER': ['NBER Working Paper', 'National Bureau of Economic Research'],
    'WP': ['Working Paper', 'Working Papers'],
}

# Create reverse mapping: full name -> abbreviation
JOURNAL_TO_ABBREV = {}
for abbrev, names in JOURNAL_ABBREVIATIONS.items():
    for name in names:
        JOURNAL_TO_ABBREV[name.lower()] = abbrev


def get_full_names(abbreviation: str) -> list:
    """Get full journal names for an abbreviation."""
    return JOURNAL_ABBREVIATIONS.get(abbreviation.upper(), [])


def get_abbreviation(full_name: str) -> str:
    """Get abbreviation for a full journal name."""
    return JOURNAL_TO_ABBREV.get(full_name.lower(), '')


def expand_search_query(query: str) -> list:
    """
    Expand a search query by replacing journal abbreviations with full names.
    Returns list of alternative queries to search.
    """
    queries = [query]
    query_upper = query.upper()

    for abbrev, full_names in JOURNAL_ABBREVIATIONS.items():
        if abbrev in query_upper:
            for full_name in full_names:
                expanded = query_upper.replace(abbrev, full_name)
                if expanded.lower() not in [q.lower() for q in queries]:
                    queries.append(expanded)

    return queries


def match_journal(query: str, journal: str) -> bool:
    """
    Check if query matches journal (considering abbreviations).
    Returns True if query matches journal name or its abbreviation.
    """
    if not journal:
        return False

    query_lower = query.lower().strip()
    journal_lower = journal.lower()

    # Direct match
    if query_lower in journal_lower:
        return True

    # Check if query is an abbreviation
    query_upper = query.upper()
    if query_upper in JOURNAL_ABBREVIATIONS:
        full_names = JOURNAL_ABBREVIATIONS[query_upper]
        for name in full_names:
            if name.lower() in journal_lower:
                return True

    # Check if journal has a known abbreviation that matches query
    abbrev = JOURNAL_TO_ABBREV.get(journal_lower, '')
    if abbrev and query_upper == abbrev:
        return True

    return False
