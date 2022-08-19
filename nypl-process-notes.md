
# Problem
Are there any OCLC holdings belonging to NYPL Reaserch libraries that should not be deleted?
Many records were not matched and because of problems ended up in a Worldcat staging area. We do not have plans to go over these records and fix the problems (too large volume) but some of them may have holdings that were deleted and we shoud try to set them again.

We need to identify OCN numbers on the deletion list that belong to RL bibs in Sierra and reverse the deletion.

## Database
### sierra_bib
	+ bibNo (primary key, digits only, no 'b' prefix)
	+ title (subfield $a, normalized, lowercase, no punctuation)
	+ isResearch (True, False, None)
	+ bibCode3 (string)
	+ bibFormat (string)

### sierra_bib_ocns (many-to-one with sierra_bib)
	+ soid (primary key)
	+ oclcNo (no prefixes, no leading zeros)
	+ bibNo (digits only, no 'b' prefix)

### oclc_match (many-to-one with sierra_bib & report)
	+ mid (primary key)
	+ bibNo (digits only, no 'b' prefix)
	+ reportId
	+ isOcnMatchingProcess (True, False)
	+ outcomeId
	+ procDate
	+ oclcNo

### report
	+ rid (primary key)
	+ handle (unique)

### status (many-to-one with oclc_match)
	+ oid (primary key)
	+ cat (unique)

### hold_delete
	+ oclcNo (primary key)
	+ title
	+ keep (True, False)


## Notes
+ records were sent multiple times to fix matching issues - consider only the last matching routine (use date in oclc_match tbl)
+ provisional records (not matched and with errors) may have holdings deleted - focus on that
+ when searching for invalid holdings deletion consider first matches on oclcNo, then tilte - review the latter
+ ignore records in Sierra that were not submitted to OCLC (exclusion note)
+ calculate number of records that were ended up as provisional or skipped because of error (possible only after ingesting all reports - multiple submission per record)
+ calculate number of records in Sierra that would benefit from inclusion of OCN number (positively matched)
  + consider local fields and the best load table to use to protect them
  + consider burden of large bib updates on other systems (NYPL Platform, other middleware, etc.)
+ sierra_bib data can be parsed from Aaron's MARC files that he turned in to OCLC
+ possibly SQLite will be a suitable match for the database
+ consider bulk inserts to database since tons of data to process
+ use OCLC BibProcessingReport to pull data

# Question
+ should we add OCN numbers to matched Sierra bibs first (full match, changed)?
+ should we care about holdings of bibs excluded from the process?


# Ideas how to proceed

