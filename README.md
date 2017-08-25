# PGCHAIN
PGCHAIN is a scheduled &amp; managed WAL archiver for PostgreSQL. It uses the 'archive_command' and it is able to show list of backups and manage them as well.

## Installation Steps
1. Make sure that your python has all the required modules installed (sys,os,sqlite3,time,ntpath,psycopg2,grp,pwd,random).
2. place the python script file in any folder that you want as long as its chmod belongs to "postgres:postgres".
3. Change the following line in the script to you own created folder name:

```
internal_home_folder = "" >> internal_home_folder = "{your_folder}"
```
THIS MUST END WITH THE BACKSLASH CHARACTER:
     THIS IS NOT GOOD: /myfolder
     THIS IS GOOD: /myfolder/

4. Create a text file called "pgchain.conf" and write the following:

```
db_path={your_folder}/pgchain.db
pgctl_path=/usr/pgsql-9.6/bin/pg_ctl # Your full path to PG_CTL binary file
```

5. Grant executable permission on the python script file:

```
chmod +x /{your_folder}/pgchain.py
```

5. Create the repository database by running the following command:

```
/{your_folder}/pgchain.py create-repo
```

## Using the 'archive_command'
This tool uses PostgreSQL's archive_command parameter to accept and store new WAL files. In order to that you need to first set the parameter 'archive_mode' to 'on'. After doing that, you need to set you 'archive_command' so it would send the WAL files to PGCHAIN. Please see the following archive command example:

```
archive_mode = on
archive_command = '{your_folder}/pgchain.py get-wal %p'
```

Remember that this will not work as long as you have created the repository.

## General Commands (--help)
You can always run PGCHAIN with the '--help' argument to see the available commands. Runnig this will show you the following:

```

  ----------------------------------------------------------------------------------------
   PGCHAIN Help
  ----------------------------------------------------------------------------------------

    General PGCHAIN Usage Syntax:
        ./pgchain.py [COMMAND] [ARGUMENTS]

    Available Commands:
        base-backup    -  Creates a base backup of the local PostgreSQL cluster.
        get-wal        -  Used in the 'archive_command' for WAL files automation.
        list-chains    -  Lists the available backup chains (base backup & WAL files).
        clear-history  -  Releases old backup chains (and deletes them from disk).
        restore-chain  -  Restores the requested chain to the local PostgreSQL cluster.
        chain-info     -  Displays information abou the requested chain.
        show-config    -  Displays the configuration information summary.
        clear-log      -  Clears (truncates) the log file.
        create-repo    -  Creates the PGCHAIN repository.
        keep-recent    -  Keeps the most recent backups (according to the given argument).
        
```

**base-backup**:
The 'base-backup' command creates a base backup (by automating pg_basebackup) and stores the file in your storage location (your folder). It then registers it in the repository database as well. Running base-backup is done **LIVE** and does not require any down time at all.

**get-wal**:
The get-wal command should be used in the archive_command parameter of your postgresql.conf file. Please see the example above. You can not run it manually as PostgreSQL determines the WAL file switch. If you would like to test it you can run "select pg_switch_xlog();" command (you need to be postgres) and the it will manually issue the WAL switch and then the archive_command will be executed (use with caution).

**list-chains**:
Lists the available chains that exists in your PGCHAIN repository. Each chain is composed of a base backup and every WAL file created after the base backup. Running this command will show you a list - see the following example:

```

  Chain Report (Last 10 Chains)

   ---------------------------------------------------------------------------------------
   ID     DATE/TIME               TOTAL SIZE (MB)     #WAL FILES    LAST RESTORE POINT
   ---------------------------------------------------------------------------------------
   1021   2017-08-25 04:02:52     98 MB               1 Files       2017-08-25 04:05:49
   1020   2017-08-23 17:14:38     161 MB              6 Files       2017-08-25 04:02:26
   1019   2017-08-23 16:54:23     145 MB              5 Files       2017-08-23 17:14:13
   1018   2017-08-23 08:27:42     145 MB              7 Files       2017-08-23 08:53:06
   1017   2017-08-23 05:51:43     145 MB              6 Files       2017-08-23 08:27:16
   1016   2017-08-21 08:49:54     199 MB              8 Files       2017-08-23 05:51:17

```

**clear-history**:
This will clear (and physically delete!) the amount of chains you decided to delete (see following command):

```
/{your_folder}/pgchain.py clear-history 1
```

this will delete the **first and oldest** backup chain in your repository and physical files. You can set the number old backups to delete in the second argument (In this example I used one).

**restore-chain**:
This command will restore a chain from your repository into your PostgreSQL data folder. THIS WILL OVERWRITE ANY EXISTING DATA YOU HAVE - USE WITH EXTREME CAUTION. As you know, you can not touch any file in the data folder without shutting down PostgreSQL first (unless you want corruption issues... and trust me... you dont!). This will shut down PostgreSQL (using the PG_CTL command) and then replace your data folder with the base backup you chose to restore (see the following command). In addition, it will create the 'recovery.conf' file and point it to restore any more WAL files from your repository (any files that were registered using the archive_command with the get-wal method - see above). It will then restart PostgreSQL which will get into recovery mode for the time period of the WAL restore and then will get out of recovery mode. See the following command as exmaple:

```
/{your_folder}/pgchain.py restore-chain 1020
```

**chain-info**:
This will display the meta-data information for the requested chain number:

```
/{your_folder}/pgchain.py chain-info 1020

  ------------------------------------------------------------------
   Chain Information
  ------------------------------------------------------------------

    Chain ID:           1020
    Chain Started:      2017-08-23 17:14:38
    Chain File Path:    /pg_chain/c1020/
    Base Backup Size:   81 MB
    Total WAL Size:     80 MB
    Total WAL Count:    6 File(s)
    Restore Command:
      ./pgchain.py restore-chain 1020
      (Always use extreme caution when deciding to restore)

```

**show-config**:
This will show you the configuration parameters of PGCHAIN:

```

  ------------------------------------------------------------------
   PGCHAIN Configuration Information
  ------------------------------------------------------------------

   PostgreSQL Version:     9.6.3
   PostgreSQL Data Folder: /var/lib/pgsql/9.6/data
   PG_CTL Executable:      /usr/pgsql-9.6/bin/pg_ctl
   PGCHAIN Version:        2017.10
   PGCHAIN Repository DB:  /pg_chain/2018.01/pgchain.db
   PGCHAIN Log Status:     Enabled

```

**clear-log**:
This will clear the log file (truncates the text file pgchain.log).

**create-repo**:
You need to run this command once you placed the python script file in your folder and changed the needed line in the python script file (see step 3 in the installation instructions above). This will create and empty repository database (using sqlite3 executable).

**keep-recent**:
This will delete all of the backups you have made (including base and WALs) **EXCEPT** for the most n recent chains you select in the second argument. An example call would look like this:

```
/{your_folder}/pgchain.py keep-recent 5
```


# USAGE EXAMPLE

After installing PGCHAIN, the following example shows you how to always maintain 5 days back of you PostgreSQL cluster.

1. Set to appropriate archive_command after the installation.
2. Create a new CRON job as the following example:

```
0 0 * * * /{your_folder}/pgchain.py keeפ-recent 5
```


