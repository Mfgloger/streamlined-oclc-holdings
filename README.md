# streamlined-oclc-holdings
 Scripts supporting OCLC streamlined holdings project


## Enhancing Sierra records (full matching only)
Legacy and vendor records (not WorldCat records) will benefit from enhacement: bringing matching record from WorldCat to overlay Sierra bib.
Full matching routine of the Streamlined Holdings project provides reports that can be used to identify these records.

First step is to combine Sierra data with OCLC report. This is to ensure the overlaying process does not loose any infomration, such as Sierra bib format code and OPAC display code. Existing call number fields (099) are protected in Sierra load tables and are not required. Minimum data needed are: Sierra bib #, Sierra bib format code, Sierra OPAC display code, and matching OCLC #. Example:

```
bibNo,oclcNo,bFormat,bDisplay
b118134449,884810765,a,-
b106624817,5240306,a,-
b113811925,1330279650,a,-
```

This data is then used to query and download full records from WorldCat using WorldCat Metadata API. Obtained records must be manipulated before the import:
+ unsupported subject headings must be removed
+ OCN prefix removed from the 001 tag (NYPL only)
+ deleted certain fields (019, 029, 263, 938, etc.)
+ add import command tag (949) with proper sierra format and OPAC display codes
+ if possible add a 909 tag (must be non-protected field in Sierra) for easy list creation in Sierra

Next, WorldCat records are loaded to Sierra using local NEW load table. Overlaid records require removal of 948 tag with "MARS" value to be picked by a authority control routine.

The enhacement process should include sending resulting records to authority work vendor to update their base file. This step is important because otherwise we run into a problem of the records being overlaid by updated by vendor bibs (BPL in quaterly update) or vendor's reports being completely off the mark, refering to non-existing data (NYPL).


#### Procedure step-by-step guide
1. Prepare all required identifiers to create appropriate Sierra lists and pull Sierra codes data and to clean up BibCrossRef reports:
	+ run `src.enhance.prepare_identifiers`  script by passing BibCrossRef reports directory. The script will a file in the `/files/enhanced/{library}/` directory: `ALL-enhance-cross-ref.cvs`
	+ this step # 1 needs to be done only once since it takes care of all data

2. Select records for processing.
	+ run `src.enhance.select_for_processing` script specifying starting row and ending row of the `ALL-enhance-cross-ref.cvs` file to be used for processing
	+ the script produces two files:
		+ `/files/enhancdd/{library}/batch-{yymmdd}-sierra-nos.csv` to be used to create a list in Sierra
		+ `/files/enhancdd/{library}/batch-{yymmdd}-oclc-nos.csv`
	+ keep track of processed records in following google sheets:
		+ [BPL](https://docs.google.com/spreadsheets/d/1fbVGzfgoG2-RTR_q0oeRlJltnzaDMCBxLL49sdOlLyE/edit?usp=sharing)
		+ NYPL

3. Create list in Sierra and export Sierra format and Sierra OPAC display codes
	+ based on `/files/enhanced/{library}/batch-{yymmdd}-sierra-nos.csv` create a list in Sierra
	+ export BIBLIOGRAPHIC RECORD #, FORMAT, OPAC DISPLAY fields to a txt file (text qualifier NONE)
	+ save exported data to `/files/enhanced/{library}/batch-{yymmdd}-sierra-codes.txt`

4. Combine data from Sierra and OCLC reports.
	+ run `src.enhance.add_sierra_codes` script
	+ the script combines data from Sierra export and from OCLC reports
	+ it produces `./files/enhance/{library}/batch-{yymmdd}-combined-data.csv`

5. Get Worldcat records for selected batch
	+ requires WorldCat Metadata API credentials
	+ uses `./files/enhance/{library}/batch-{yymmdd}-combined-data.csv` file to obtain MARCXML files from the API
	+ outputs obtain records to `./files/enhance/{library}/batch-{yymmdd}-worldcat-bibs.mrc`
	+ adds 907 (BPL) and 949 fields to downloaded records that specify Sierra matchpoint and import configuration (this preseves Sierra Format and OPAC Display codes)
	+ adds initials `SHPbot` in 947 (BPL)

6. Manipulate Worldcat records
	+ run script `src.enhance.manipulate_worldcat_records` to clean up subject headings (only terms from supported by BPL and NYPL vocabularies are kept on bibs) and to remove some unwanted MARC tags.
	+ the script creates `./files/enhance/{library}/streamlined-holdings-enhancement-batch-{yymmdd}.mrc` that is ready to be loaded to Sierra

7. Import produced final file to Sierra and overlay original records with records from WorldCat.
	+ use `./files/enhance/{library}/streamlined-holdings-enhancement-batch-{yymmdd}.mrc` file



	BACKSTAGE SEARCH MUST BE UPDATED TO EXCLUDE ENHANCED RECORDS - they will be submitted separately.