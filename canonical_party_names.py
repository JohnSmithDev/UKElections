#!/usr/bin/env python3
"""
Map party names/IDs that appear in the CSVs to canonical names.

This is to cover situations like the 2015 CSV having "Green" in the "Party name
identifier" and "Party abbreviation" columns, but "Green Party" in the
2017 CSV "Party Identifer" (sic) column"

Usage:
This currently only maps differences, so *DON'T* do this:

  canonical_party = CANONICAL_PARTY_NAMES[whatever]

Instead do:

  canonical_party = CANONICAL_PARTY_NAMES.get(whatever, whatever)

TODO (maybe): add all party names, in which case the regular dict access might
be OK, although I suspect the number of independents and minor parties will
make this too prone to breakage.
"""

# Order these as follows:
# * "Main" parties that stand in England, Scotland and Wales
# * Scottish parties (primarily SNP, but maybe there are smaller ones?)
# * Welsh parties (primarily Plaid, but maybe there are smaller ones?)
# * Northern Ireland parties
# * Independents, speaker, etc

CANONICAL_PARTY_NAMES = {
    'Green Party': 'Green',

    # Not ideal, but makes life easier (NB: 2015 CSV uses the accented version
    # TODO: HTML entity variant?
    'Sinn Féin': 'Sinn Fein'
}
