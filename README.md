Something that works is the goal, ignore all the spaghetti

## Different Tiers

### TIER_1_RSS (Easiest):

- Source provides RSS/Atom feed
- Need to parse xml, no html scraping needed

### TIER_2_STATIc (Medium):

- No RSS feed, but all is not last because http request
- Need to parse HTML:(, but okay

### TIER_3_BROWSER (Hardest):

- Site blocks requests OR uses JavaScript to load content
- Needs full browser automation
