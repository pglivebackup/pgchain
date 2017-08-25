#!/bin/python
import sys,os,sqlite3,time,ntpath,psycopg2,grp,pwd
from random import randint

class color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

def is_folder_belongs_to_postgres(folderPath):
	stat_info = os.stat(folderPath)
	uid = stat_info.st_uid
	gid = stat_info.st_gid
	user = pwd.getpwuid(uid)[0]
	group = grp.getgrgid(gid)[0]
	r = 0
	if ((str(user).lower() == "postgres") and (str(group).lower() == "postgres")):
		r = 1
	return r

print ""
print " PG_CHAIN v2017.10 (MIT License)"
print " Created by Doron Yaary (pglivebackup@gmail.com)"

if ((len(sys.argv) == 2) and (str(sys.argv[1]).lower() == "--help")):
	print color.BOLD + "  ----------------------------------------------------------------------------------------" + color.END
	print color.BOLD + "   PGCHAIN Help" + color.END
	print color.BOLD + "  ----------------------------------------------------------------------------------------" + color.END
	print ""
	print "    " + color.UNDERLINE + "General PGCHAIN Usage Syntax:" + color.END
	print "        ./pgchain.py [COMMAND] [ARGUMENTS]"
	print ""
	print "    " + color.UNDERLINE + "Available Commands:" + color.END
	print "        " + color.BOLD + "base-backup  " + color.END + "  -  Creates a base backup of the local PostgreSQL cluster."
	print "        " + color.BOLD + "get-wal      " + color.END + "  -  Used in the 'archive_command' for WAL files automation."
	print "        " + color.BOLD + "list-chains  " + color.END + "  -  Lists the available backup chains (base backup & WAL files)."
	print "        " + color.BOLD + "clear-history" + color.END + "  -  Releases old backup chains (and deletes them from disk)."
	print "        " + color.BOLD + "restore-chain" + color.END + "  -  Restores the requested chain to the local PostgreSQL cluster."
	print "        " + color.BOLD + "chain-info   " + color.END + "  -  Displays information abou the requested chain."
	print "        " + color.BOLD + "show-config  " + color.END + "  -  Displays the configuration information summary."
	print "        " + color.BOLD + "clear-log    " + color.END + "  -  Clears (truncates) the log file."
	print "        " + color.BOLD + "create-repo  " + color.END + "  -  Creates the PGCHAIN repository."
	print "        " + color.BOLD + "keep-recent  " + color.END + "  -  Keeps the most recent backups (according to the given argument)."
	print ""
	sys.exit(0)

con = None
internal_db_path = ""
internal_pgctl_path = ""
internal_log_enabled = ""
# The following line needs to be changed by you (see installation notes on GitHub)
internal_home_folder = "/pg_chain/"
print ""

if ((len(sys.argv) == 2) and (str(sys.argv[1]).lower() == "create-repo")):
	if (os.path.isfile(internal_home_folder + "pgchain.db") == True):
		print "   " + color.BOLD + "ERROR:" + color.END + " The repository file (pgchain.db) already exists."
		print "   INFO: If you plan on this name after all, please backup the current one and move it elsewhere first."
		print ""
		sys.exit(0)
	print "  " + color.BOLD + "Please Confirm:" + color.END
	print "  --------------------------------------------------------------"
	print "   This will create the repository database by using the 'sqlite3' command."
	print "   The repostiroty database will be created here: " + color.UNDERLINE + str(internal_home_folder) + "pgchain.db" + color.END
	ap = raw_input("   Please approve (Y/N): ")
	ap = ap.lower()
	if (ap != "y"):
		print ""
		print "   You did not approve - nothing changed/created. Quiting."
		print ""
		sys.exit(0)
	print ""
	sql = " "
	sql = sql + "CREATE TABLE chain_sequence (seq_next_id int not null); "
	sql = sql + "CREATE TABLE chains (chain_id int not null, base_backup_full_path varchar(512) not null, chain_start_timestamp datetime not null); "
	sql = sql + "CREATE TABLE file_sequence (file_next_id int not null); "
	sql = sql + "CREATE TABLE wal_files (file_id int not null, file_full_path varchar(512) not null, file_timestamp datetime not null, file_size_mb int not null); "
	sql = sql + "CREATE TABLE chain_files (file_id int not null, parent_chain_id int not null, file_type char(1) not null, file_timestamp datetime not null, file_full_path varchar(512), file_size_mb int); "
	sql = sql + "INSERT INTO file_sequence VALUES (1001); "
	sql = sql + "INSERT INTO chain_sequence VALUES (1001); "
	print ""
	print "   Creating repository..."
	os.system("echo '" + str(sql) + "' | sqlite3 " + str(internal_home_folder) + "pgchain.db")
	print "   Done."
	print ""
	sys.exit(0)

if (os.path.isfile(internal_home_folder + "pgchain.conf") == False):
	print "  " + color.BOLD + "ERROR:" + color.END + " The configuration files could not be found (pgchain.conf)"
	print "  HINT: Read the documentation regarding the configuration file."
	print ""
	sys.exit(0)

with open(internal_home_folder + "pgchain.conf") as f:
	for line in f:
		if (line != ""):
			if not line.startswith("#"):
				v = line.rstrip()
				if (v.lower().startswith("db_path=")):
					internal_db_path = v.replace("db_path=","")
					if (os.path.isfile(internal_db_path) == False):
						print "  " + color.BOLD + "ERROR:" + color.END + " The repository file (db file) could not be found."
						print "  HINT:  The configuration file directs to: " + internal_db_path
						print "  READ:  If you never created the repository please use the 'create-repo' argument first."
						print ""
						sys.exit(0)
					try:
						con = sqlite3.connect(internal_db_path)
					except:
						print "  " + color.BOLD + "ERROR:" + color.END + " Could not open the database file (unknown reason)"
						print "  HINT:  The configuration file directs to: " + internal_db_path
						print ""
						sys.exit(0)
				if (v.lower().startswith("pgctl_path=")):
					internal_pgctl_path = v.replace("pgctl_path=","")
					if (os.path.isfile(internal_pgctl_path) == False):
						print "  " + color.BOLD + "ERROR:" + color.END + " The path for PG_CTL is wrong (in the configuration file)."
						print ""
						sys.exit(0)
				if (v.lower().startswith("log_enabled=")):
					internal_log_enabled = v.replace("log_enabled=","")
					if ((internal_log_enabled != "1") and (internal_log_enabled != "0")):
						print "  " + color.BOLD + "ERROR:" + color.END + " the log enabled/disabled parameter value is invalid."
						print "  HINT:  Should be 0 or 1 - the given value is: " + internal_log_enabled
						print ""
						sys.exit(0)
				'''
				if (v.lower().startswith("home_folder=")):
					internal_home_folder = v.replace("home_folder=","")
					if (os.path.isdir(internal_home_folder) == False):
						print "  " + color.BOLD + "ERROR:" + color.END + " the home folder parameter value is invalid."
						print "  HINT:  The given folder (" + internal_home_folder + ") is not a folder..."
						print ""
						sys.exit(0)
					if (is_folder_belongs_to_postgres(internal_home_folder) == 0):
						print "  " + color.BOLD + "ERROR:" + color.END + " The home folder does not belong to the user postgres."
						print "  HINT:  This can be fixed by running 'sudo chown -R postgres:postgres " + internal_home_folder + "'."
						print ""
						sys.exit(0)
					if (internal_home_folder.endswith("/") == True):
						internal_home_folder = internal_home_folder[:-1]
				'''

# The following two lines are for backward compatibility and will be removed in future versions
is_nolog = int(internal_log_enabled)
conf_pg_ctl = internal_pgctl_path
# ---------------------------------------------------------------------------------------------

def adjust_string_size(mystring,maxlength):
	a = ""
	if (mystring == None):
		a = ""
	if (mystring != None):
		a = mystring
	while (len(a) < maxlength):
		a = a + str(" ")
	return a

def report_log_line(logline):
	ts = ""
	ts = str(time.strftime("%x")) + " " + str(time.strftime("%X"))
	os.system("echo '" + str(ts) + ": " + str(logline) + "' >> " + internal_home_folder + "pgchain.log")
	return 0

if (len(sys.argv) < 2):
	print " ERROR: Bad arguments or missing arguments."
	print ""
	con.close()
	sys.exit(0)

if (str(sys.argv[1]).lower() == "clear-log"):
	os.system("echo > " + internal_home_folder + "pgchain.log")
	print " INFO: The log was cleared."
	print ""
	sys.exit(0)

if (str(sys.argv[1]).lower() == "base-backup"):
	report_log_line("==================================================================")
	report_log_line("STARTING BASE BACKUP")
	report_log_line("==================================================================")
	newchainid = 0
	cur = con.execute("select max(seq_next_id) from chain_sequence;")
	for row in cur:
		newchainid = int(row[0])
	newchainid = newchainid + 1
	con.execute("update chain_sequence set seq_next_id = " + str(newchainid) + ";")
	con.commit()
	report_log_line("Creating folders for new chain (ID = " + str(newchainid) + ")")
	os.system("mkdir -p " + internal_home_folder + "/c" + str(newchainid))
	os.system("mkdir -p " + internal_home_folder + "/c" + str(newchainid) + "/base_tmp")
	report_log_line("Taking base backup...")
	os.system("pg_basebackup --xlog-method=stream --format=p -D " + internal_home_folder + "/c" + str(newchainid) + "/base_tmp")
	report_log_line("Compressing the base backup...")
	os.system("cd " + internal_home_folder + "/c" + str(newchainid) + "/base_tmp && tar -zcf base" + str(newchainid) + ".tar .")
	os.system("mv " + internal_home_folder + "/c" + str(newchainid) + "/base_tmp/base" + str(newchainid) + ".tar " + internal_home_folder + "/c" + str(newchainid) + "/base" + str(newchainid) + ".tar")
	report_log_line("Removing un-needed files...")
	os.system("rm -rf " + internal_home_folder + "/c" + str(newchainid) + "/base_tmp")
	report_log_line("Registering new chain...")
	basesize = 0
	basesize = os.path.getsize(internal_home_folder + "/c" + str(newchainid) + "/base" + str(newchainid) + ".tar")
	basesize = ((basesize / 1024)/1024)
	con.execute("insert into chains values (" + str(newchainid) + ",'" + internal_home_folder + "/c" + str(newchainid) + "/',datetime('now'));")
	con.commit()
	newfileid = 0
	cur = con.execute("select max(file_next_id) from file_sequence;")
	for row in cur:
		newfileid = int(row[0])
	newfileid = newfileid + 1
	con.execute("update file_sequence set file_next_id = " + str(newfileid) + ";")
	con.commit()
	con.execute("insert into chain_files values (" + str(newfileid) + "," + str(newchainid) + ",'B',datetime('now'),'" + internal_home_folder + "/c" + str(newchainid) + "/base" + str(newchainid) + ".tar'," + str(basesize) + ");")
	con.commit()
	report_log_line("Done with base backup.")
	print ""
	con.close()
	sys.exit(0)

if (str(sys.argv[1]).lower() == "get-wal"):
	report_log_line("==================================================================")
	report_log_line("GET WAL ACTION")
	report_log_line("==================================================================")
	if (len(sys.argv) < 3):
		report_log_line("ERROR: Could not register WAL file as thesecond argument is missing.")
		con.close()
		sys.exit(0)
	if (str(sys.argv[2]) == ""):
		report_log_line("ERROR: Could not register WAL file as thesecond argument is missing.")
		con.close()
		sys.exit(0)
	if (os.path.isfile(str(sys.argv[2])) == False):
		report_log_line("ERROR: The WAL file argument is no a file. check the archive_command in postgresql.conf")
		con.close()
		sys.exit(0)
	curchain = 0
	cur = con.execute("select max(chain_id) from chains;")
	for row in cur:
		curchain = int(row[0])
	if (curchain == None):
		con.close()
		report_log_line("ERROR: Could not find a valid chain (perhaps no base-backup was done?)")
		sys.exit(0)
	walsize = 0
	walsize = os.path.getsize(str(sys.argv[2]))
	walsize = ((walsize / 1024) / 1024)
	walshortname = ""
	walshortname = ntpath.basename(str(sys.argv[2]))
	newfileid = 0
	cur = con.execute("select max(file_next_id) from file_sequence;")
	for row in cur:
		newfileid = int(row[0])
	newfileid = newfileid + 1
	cur.execute("update file_sequence set file_next_id = " + str(newfileid) + ";")
	con.commit()
	report_log_line("Accepting WAL file [" + str(sys.argv[2]) + "] with size = " + str(walsize) + "MB to chain ID = " + str(curchain) + ".")
	report_log_line("Copying the WAL file [" + str(sys.argv[2]) + "] to chain folder [" + internal_home_folder + "/c" + str(curchain) + "/].")
	os.system("cp " + str(sys.argv[2]) + " " + internal_home_folder + "/c" + str(curchain) + "/")
	cur.execute("insert into chain_files values (" + str(newfileid) + "," + str(curchain) + ",'W',datetime('now'),'" + internal_home_folder + "/c" + str(curchain) + "/" + str(walshortname) + "'," + str(walsize) + ");")
	con.commit()
	con.close()
	report_log_line("Done.")
	print ""

if (str(sys.argv[1]).lower() == "list-chains"):
	print "  Chain Report (Last 10 Chains)"
	print ""
	print color.BOLD + "   ---------------------------------------------------------------------------------------" + color.END
	print color.BOLD + "   ID     DATE/TIME               TOTAL SIZE (MB)     #WAL FILES    LAST RESTORE POINT" + color.END
	print color.BOLD + "   ---------------------------------------------------------------------------------------" + color.END
	cur = con.execute("select a.chain_id,a.chain_start_timestamp,(select sum(b.file_size_mb) from chain_files b where b.parent_chain_id = a.chain_id),a.base_backup_full_path,(select count(*) from chain_files c where c.parent_chain_id = a.chain_id and c.file_type = 'W'),(select  max(file_timestamp) from chain_files c where c.parent_chain_id = a.chain_id and c.file_type = 'W') from chains a order by chain_id desc limit 10;")
	for row in cur:
		ln = ""
		ln = "   " + adjust_string_size(str(row[0]),7) + adjust_string_size(str(row[1]),24)
		if (str(row[2]) == ""):
			ln = ln + adjust_string_size(str("MB"),20)
		if (str(row[2]) != ""):
			ln = ln + adjust_string_size(str(str(row[2]) + " MB"),20)
		ln = ln + adjust_string_size(str(row[4]) + " Files",14)
		if (str(row[5]) == "None"):
			ln = ln + str(row[1])
		if (str(row[5]) != "None"):
			ln = ln + str(row[5])
		print ln
	print ""
	con.close()
	sys.exit(0)

if (str(sys.argv[1]).lower() == "clear-history"):
	report_log_line("==================================================================")
	report_log_line("CLEAR HISTORY TASK")
	report_log_line("==================================================================")
	if (len(sys.argv) < 3):
		report_log_line("ERROR: Could not clear history - missing argument.")
		print "  ERROR: Could not clear history - missing argument."
		print ""
		con.close()
		sys.exit(0)
	if (str(sys.argv[2]).isdigit() == False):
		report_log_line("ERROR: Could not clear history - invalid argument (perhaps string instead of number?).")
		print "  ERROR: Could not clear history - invalid argument."
		print ""
		con.close()
		sys.exit(0)
	chainsback = int(sys.argv[2])
	report_log_line("Starting to remove/delete " + str(chainsback) + " oldest chains.")
	report_log_line("INFO: This is due to a command line request that executed the clear-history command.")
	chainsarray = ""
	cur = con.execute("select chain_id from chains order by chain_id asc limit " + str(chainsback) + ";")
	for row in cur:
		report_log_line("INFO: Deleting chain #" + str(row[0]) + " from disk.")
		os.system("rm -rf " + internal_home_folder + "/c" + str(row[0]))
		chainsarray = chainsarray + str(row[0]) + ";"
	tmp = chainsarray.split(';')
	for ch in tmp:
		if ((str(ch) != "") and (ch != None)):
			report_log_line("Removing repository data for chain #" + str(ch) + " that was cleared.")
			cur.execute("delete from chains where chain_id = " + str(ch) + ";")
			con.commit()
			cur.execute("delete from chain_files where parent_chain_id = " + str(ch) + ";")
			con.commit()
	report_log_line("Done.")
	print ""
	print "   The repository history was removed."
	print ""
	con.close()
	sys.exit(0)

if (str(sys.argv[1]).lower() == "restore-chain"):
	if (is_nolog == 1):
		print "  INFO: Canceling the '--nolog' - restore must be written to the log."
	if (len(sys.argv) < 3):
		print "  ERROR: Bad/missing arguments (missing the chain number). Quiting."
		print "  HINT:  Use the --help switch for more information."
		print ""
		con.close()
		sys.exit(0)
	if (str(sys.argv[2]).isdigit() == False):
		print "  ERROR: Bad/missing arguments (missing the chain number). Quiting."
		print "  HINT:  Use the --help switch for more information."
		print ""
		con.close()
		sys.exit(0)
	restore_check = 0
	datadir = ""
	pg = psycopg2.connect(host="127.0.0.1", port="5432")
	pgcur = pg.cursor()
	pgcur.execute("select pg_is_in_recovery()::int;")
	pgrow = pgcur.fetchone()
	restore_check = int(pgrow[0])
	pgcur.execute("select setting from pg_settings where name = 'data_directory';")
	pgrow = pgcur.fetchone()
	datadir = str(pgrow[0])
	pgrow = None
	pgcur = None
	pg.close()
	pg = None
	if (restore_check == 1):
		print "  ERROR: PostgreSQL is currently in restore mode - wait until it finishes first."
		print "  HINT:  Please check why PostgreSQL is in restore mode if you are now trying to restore..."
		print ""
		con.close()
		sys.exit(0)
	chain_check = 0
	cur = con.execute("select count(*) from chains where chain_id = " + str(sys.argv[2]) + ";")
	for row in cur:
		if ((row[0] != None) and (str(row[0]) != "")):
			chain_check = int(row[0])
	if (chain_check == 0):
		print "  ERROR: Could not find chain #" + str(sys.argv[2]) + "."
		print "  HINT:  Check your chains with the --list-chains argument for more information."
		print ""
		con.close()
		sys.exit(0)
	print color.PURPLE + "  ============================================================================================================" + color.END
	print color.PURPLE + "  IMPORTANT WARNING:" + color.END
	print color.PURPLE + "  ============================================================================================================" + color.END
	print "  The following action will do the following actions - you must approve them first:"
	print "     1) Shut down PostgreSQL (by using pg_ctl)"
	print "     2) Take a full backup for the current layout (BEFORE the restore process) by moving the data directory (quicker)"
	print "     3) Restore the base backup (you have chosen to restore chain #" + str(sys.argv[2]) + ")"
	print "     4) Create the recovery configuration file (to keep restoring the WAL files)"
	print "     5) Start PostgreSQL server (which will go into recovery mode and then will resume normal activity)"
	print ""
	print "  Please read this as well:"
	print "  ============================================================================================================"
	print "   Should any error occur in the process the instance will not be able to start and there is a chance"
	print "   of data-loss. In that case you will have to revert to the base copy made on step 2 (see above) which may"
	print "   get you back to the prior state."
	print ""
	apr = raw_input("  PLEASE APPROVE " + color.BOLD + "(Y/N)" + color.END + ": ")
	if (str(apr).lower() != "y"):
		print "  INFO: Quiting as you didn't approve the above changes."
		print ""
		con.close()
		sys.exit(0)
	report_log_line("==================================================================")
	report_log_line("RESTORE CHAIN ACTION")
	report_log_line("==================================================================")
	report_log_line("Stopping PostgreSQL now!")
	os.system(conf_pg_ctl + " stop -s -D " + str(datadir))
	temp_folder_name = str(randint(10000,99999))
	temp_folder_name = str(datadir).replace(ntpath.basename(datadir),temp_folder_name)
	report_log_line("Changing the 'data' folder name to a temporary name (" + str(temp_folder_name) +")")
	os.system("mv " + str(datadir) + " " + str(temp_folder_name))
	report_log_line("Creating new directory with the old name (" + str(datadir) + ")")
	os.system("mkdir " + str(datadir))
	os.system("chmod -R 700 " + str(datadir))
	report_log_line("Getting base backup TAR file from PGCHAIN repostitory folder")
	os.system("cp " + internal_home_folder + "/c" + str(sys.argv[2]) + "/base" + str(sys.argv[2]) + ".tar " + str(datadir))
	report_log_line("Extracting files from TAR archive")
	os.system("tar -xf " + str(datadir) + "/base" + str(sys.argv[2]) + ".tar -C " + str(datadir))
	report_log_line("Removing the TAR file (as it is not needed anymore)")
	os.system("rm -rf " + str(datadir) + "/base" + str(sys.argv[2]) + ".tar")
	report_log_line("Creating recovery.conf file before starting the service again")
	os.system("touch " + str(datadir) + "/recovery.conf")
	os.system("echo \"restore_command = 'cp " + internal_home_folder + "/c" + str(sys.argv[2]) + "/%f \"%p\"'\" >> " + str(datadir) + "/recovery.conf")
	report_log_line("Assuring chmod 700 to the data folder")
	os.system("chmod -R 700 " + str(datadir))
	report_log_line("Removing temporary folder")
	os.system("rm -rf " + str(temp_folder_name))
	report_log_line("Starting PostgreSQL again")
	os.system(conf_pg_ctl + " -D " + str(datadir) + " start & ")
	print ""
	con.close()
	con = None
	sys.exit(0)

if (str(sys.argv[1]).lower() == "chain-info"):
	if (len(sys.argv) < 3):
		print "  ERROR: Bad/missing arguments (missing the chain number). Quiting."
		print "  HINT:  Use the --help switch for more information."
		print ""
		con.close()
		sys.exit(0)
	chain_check = 0
	ch = str(sys.argv[2])
	cur = con.execute("select count(*) from chains where chain_id = " + str(ch) + ";")
	for row in cur:
		if ((row[0] != None) and (str(row[0]) != "")):
			chain_check = int(row[0])
	if (chain_check == 0):
		print "  ERROR: The chain number you provided doesn't exist."
		print ""
		con.close()
		sys.exit(0)
	print color.BOLD + "  ------------------------------------------------------------------" + color.END
	print color.BOLD + "   Chain Information" + color.END
	print color.BOLD + "  ------------------------------------------------------------------" + color.END
	cur = con.execute("select chain_id,base_backup_full_path,chain_start_timestamp,(select file_size_mb from chain_files where parent_chain_id = " + str(ch) + " and file_type = 'B'),(select sum(file_size_mb) from chain_files where parent_chain_id = " + str(ch) + " and file_type = 'W'),(select count(*) from chain_files where parent_chain_id = " + str(ch) + " and file_type = 'W') from chains where chain_id = " + str(ch) + ";")
	row = cur.fetchone()
	print ""
	print "    Chain ID:           " + color.BOLD + str(ch) + color.END
	print "    Chain Started:      " + color.BOLD + str(row[2]) + color.END
	print "    Chain File Path:    " + color.BOLD + str(row[1]) + color.END
	print "    Base Backup Size:   " + color.BOLD + str(row[3]) + color.END + " MB"
	print "    Total WAL Size:     " + color.BOLD + str(row[4]) + color.END + " MB"
	print "    Total WAL Count:    " + color.BOLD + str(row[5]) + color.END + " File(s)"
	print "    " + color.UNDERLINE + "Restore Command:" + color.END
	print "      ./pgchain.py restore-chain " + str(ch)
	print "      (Always use extreme caution when deciding to restore)"
	print ""
	print ""
	con.close()
	con = None
	sys.exit(0)

if (str(sys.argv[1]).lower() == "show-config"):
	print color.BOLD + "  ------------------------------------------------------------------" + color.END
	print color.BOLD + "   PGCHAIN Configuration Information" + color.END
	print color.BOLD + "  ------------------------------------------------------------------" + color.END
	pg = psycopg2.connect(host="127.0.0.1", port="5432")
	pgcur = pg.cursor()
	pgcur.execute("select setting from pg_settings where name = 'server_version';")
	pgrow = pgcur.fetchone()
	print ""
	print "   PostgreSQL Version:     " + color.BOLD + str(pgrow[0]) + color.END
	pgcur = pg.cursor()
	pgcur.execute("select setting from pg_settings where name = 'data_directory';")
	pgrow = pgcur.fetchone()
	print "   PostgreSQL Data Folder: " + color.BOLD + str(pgrow[0]) + color.END
	pg.close()
	print "   PG_CTL Executable:      " + color.BOLD + internal_pgctl_path + color.END
	print "   PGCHAIN Version:        " + color.BOLD + "2017.10 Beta2" + color.END
	print "   PGCHAIN Repository DB:  " + color.BOLD + internal_db_path + color.END
	if (internal_log_enabled == "0"):
		print "   PGCHAIN Log Status:     " + color.BOLD + "Disabled" + color.END
	if (internal_log_enabled == "1"):
		print "   PGCHAIN Log Status:     " + color.BOLD + "Enabled" + color.END
	print ""
	con.close()
	con = None
	sys.exit(0)

if (str(sys.argv[1]).lower() == "keep-recent"):
	if (len(sys.argv) < 3):
		print "  ERROR: Bad/missing arguments (missing the chain number). Quiting."
		print "  HINT:  Use the --help switch for more information."
		print ""
		con.close()
		sys.exit(0)
	if (str(sys.argv[2]).isdigit() == False):
		print "  ERROR: Bad/missing arguments (missing the chain number). Quiting."
		print "  HINT:  Use the --help switch for more information."
		print ""
		con.close()
		sys.exit(0)
	if (int(sys.argv[2]) == 0):
		print "  ERROR: Could not keep zero chains.. that would mean delete the entire backup repository."
		print "  HINT:  Use the --help switch for more information."
		print ""
		con.close()
		sys.exit(0)
	requested_chain_count = int(sys.argv[2])
	actual_chain_count = 0
	cur = con.cursor()
	cur.execute("select count(*) from chains;")
	row = cur.fetchone()
	actual_chain_count = int(row[0])
	if (requested_chain_count > actual_chain_count):
		print "  " + color.BOLD + "ERROR:" + color.END + " The requested chains to keep if larger than the actual chains."
		print ""
		con.close()
		sys.exit(0)
	kepts = []
	removs = []
	cur.execute("select chain_id from chains order by chain_id desc limit " + str(requested_chain_count) + ";")
	for row in cur:
		kepts.append(str(row[0]))
	cur.execute("select chain_id from chains order by chain_id desc;")
	for row in cur:
		if (str(row[0]) not in kepts):
			removs.append(str(row[0]))
	for chain in removs:
		print "  Removing chain #" + str(chain) + "..."
		os.system("rm -rf " + str(internal_home_folder) + "c" + str(chain))
		os.system("echo 'delete from chains where chain_id = " + str(chain) + ";' | sqlite3 " + str(internal_home_folder) + "pgchain.db")
		os.system("echo 'delete from chain_files where parent_chain_id = " + str(chain) + ";' | sqlite3 " + str(internal_home_folder) + "pgchain.db")
	print "  Done."
	print ""
	con.close()
	sys.exit(0)

con.close()
con = None

