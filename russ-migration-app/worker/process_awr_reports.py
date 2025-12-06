
import os
import sys

############ Local script execution parameter #############

# local_dev = False
local_dev = True    # activate for local python execution1
debug = False
# debug = True        # activate for additional debug output1

# Some initializations
sqlSource = 'sqlOrdered'    # get SQLs from AWR section 'SQL Statistics - Top N SQL ordered by *'
outFileBase = 'output_1'

inFolder = sys.argv[1]
outFolder = sys.argv[2]
# output = os.path.join(local_out_path,output)
fileNames = os.listdir(inFolder)
files = []
for f in fileNames:
    files.append(os.path.join(inFolder, f))
fileTexts = []
# read the files content
for fileName in files:
    if fileName.endswith('.html') or fileName.endswith('.lst'):
        with open(fileName, 'r', encoding="utf8", errors='ignore') as f:
            fileTexts.append(f.read())



########## Objects used for input files ############

# VMware ESX host information fetched from RV Tools output RVTools_tabvHost.csv
# RV tools csv columns [csv column name, internal used column name]
rvHostCols = [
    ['HT Available', 'esx_ht_available'],       # Whether or not hyperthreading optimization is available
    ['HT Active', 'esx_ht_active'],             # Whether or not the CPU scheduler is currently treating hyperthreads as schedulable resources
    ['CPU Model', 'esx_cpu_model'],             # ESX CPU model
    ['Speed', 'esx_cpu_speed'],                 # The speed of the CPU cores.    ['# CPU', 'esx_cpu_num'],                   # RVTools_tabvHost.csv
    ['# CPU', 'esx_cpu_num'],                   # Number of physical CPU
    ['Cores per CPU', 'esx_cores_per_cpu'],     # Number of cores per physical CPU
    ['# Cores', 'esx_cores'],                   # Number of cores
    ['CPU usage %', 'esx_cpu_usage_pct'],       # Aggregated CPU usage across all cores on the host in %
    ['# Memory', 'esx_memory_mb'],              # Total amount of physical memory on the host
    ['Memory usage %', 'esx_memory_usage_pct'], # Physical memory usage on the host in %
    # ['# VMs total', 'esx_vm_num'],              # Total number of VMs on this host
    # ['# VMs', 'esx_vm_run'],                    # The number of running VMs on this host
    # ['VMs per core', 'esx_vm_run_per_core'],    # The number of running VMâ€™s per core on this host
    # ['# vCPUs', 'esx_mem_usage_pct'],           # Total number of running virtual CPUs on this host
    # ['vCPUs per core', 'esx_mem_usage_pct'],    # The number of active virtual cpu's per core
    # ['vRAM', 'esx_mem_usage_pct'],              # Total amount of virtual RAM allocated to all running VMs
    # ['VM Used memory', 'esx_mem_vm_used']       # Guest memory: Total amount of memory in MiB, recently accessed
]

# Other VMWare VM guest information available from RV Tools output:
# - RVTools_tabvInfo.csv (actually not used)
#   -> CPU's - Number of processors in the virtual machine.
#   -> Memory- Memory size of the virtual machine, in megabytes.
# - RVTools_tabvCPU.csv (actually not used)
#   -> details about VMWare cpu management
# - RVTools_tabvMemory.csv (actually not used)
#   -> details about VMWare memory management

# Database size csv columns [csv column name, internal used column name]
# Data from csv are not mapped to internal column names if an empty string is defined (e.g. used for join columns)
dbSizeCols = [
    ['DB_NAME', ''],                # column only used to join other data
    ['DB_UNAME', ''],               # column only used to join other data
    # ['BRUTTO_GB', ''],
    # ['FREE_GB', ''],
    ['NETTO_GB', 'db_size_gb'],
    ['TABLE_GB', 'db_tables_gb'],
    ['INDEX_GB', 'db_indexes_gb'],
]

########## Objects used for output files ###########

# CSV and XLS output file column definition { <csv column position>, <csv column name>, <xls column position>, <xls column name> }
# - ccol  == csv output file - column position
# - cname == csv output file - column name
# - xcol  == xls output file - column position
# - xname == xls output file - column name
# Attention:
# - Csv column names (<cname> values) are also used for python internal field references.
#   -> Therefore csv column names should not be changed!
# - Csv output file is used for PowerBI data import and therefore should have a stable format!
#   -> Please do not change the csv column names (<cname> values) and csv column order (<ccol> values).
#   -> But you can add new columns at the end of the csv column definition (ccol > max(ccol))
output_columns = [
    # General information
    {'ccol': 1, 'cname': 'id', 'xcol': 1, 'xname': 'ID'},
    {'ccol': 2, 'cname': 'filename', 'xcol': 2, 'xname': 'Filename'},
    {'ccol': 3, 'cname': 'parent', 'xcol': 3, 'xname': 'Parent'},
    {'ccol': 4, 'cname': 'db_type', 'xcol': 4, 'xname': 'Type'},
    {'ccol': 5, 'cname': 'status', 'xcol': 5, 'xname': 'Status'},
    {'ccol': 6, 'cname': 'db_snap_begin_time', 'xcol': 6, 'xname': 'Begin Snap'},
    {'ccol': 7, 'cname': 'db_snap_end_time', 'xcol': 7, 'xname': 'End Snap'},
    {'ccol': 8, 'cname': 'db_edition', 'xcol': 8, 'xname': 'Edition'},
    {'ccol': 9, 'cname': 'db_release', 'xcol': 9, 'xname': 'Release'},
    {'ccol': 10, 'cname': 'db_cdb', 'xcol': 10, 'xname': 'CDB'},
    {'ccol': 11, 'cname': 'db_rac', 'xcol': 11, 'xname': 'RAC'},
    {'ccol': 12, 'cname': 'db_inst_num', 'xcol': 12, 'xname': 'Number of Instances'},
    {'ccol': 13, 'cname': 'db_inst_id', 'xcol': 13, 'xname': 'Instance ID'},
    {'ccol': 14, 'cname': 'db_name', 'xcol': 14, 'xname': 'DB Name'},
    {'ccol': 15, 'cname': 'db_uname', 'xcol': 15, 'xname': 'DB Unique Name'},
    {'ccol': 16, 'cname': 'db_inst_name', 'xcol': 16, 'xname': 'Instance Name'},
    {'ccol': 17, 'cname': 'host_name', 'xcol': 17, 'xname': 'Host Name'},
    {'ccol': 18, 'cname': 'platform', 'xcol': 18, 'xname': 'Platform'},
    {'ccol': 69, 'cname': 'db_id', 'xcol': 69, 'xname': 'DB ID'},

    # CPU information
    {'ccol': 19, 'cname': 'host_cpu_num', 'xcol': 19, 'xname': 'Host CPUs'},
    {'ccol': 20, 'cname': 'db_cpu_count', 'xcol': 20, 'xname': 'DB cpu_count'},
    {'ccol': 21, 'cname': 'db_cpu_num', 'xcol': 22, 'xname': 'DB CPUs'},
    {'ccol': 22, 'cname': 'db_cpu_usage_pct', 'xcol': 21, 'xname': 'DB CPU usage %'},

    # Memory information
    {'ccol': 23, 'cname': 'host_memory_mb', 'xcol': 23, 'xname': 'Host Memory (mb)'},
    {'ccol': 24, 'cname': 'db_sga_usage_mb', 'xcol': 24, 'xname': 'SGA use (mb)'},
    {'ccol': 25, 'cname': 'db_pga_usage_mb', 'xcol': 25, 'xname': 'PGA use (mb)'},
    {'ccol': 26, 'cname': 'db_memory_mb', 'xcol': 26, 'xname': 'DB Memory (mb)'},
    {'ccol': 27, 'cname': 'db_memory_usage_pct', 'xcol': 27, 'xname': 'DB Memory usage %'},

    # IO information
    {'ccol': 28, 'cname': 'db_physical_read_total_io_ps', 'xcol': 28, 'xname': 'DB io read (iops)'},
    {'ccol': 29, 'cname': 'db_physical_write_total_io_ps', 'xcol': 29, 'xname': 'DB io write (iops)'},
    {'ccol': 30, 'cname': 'db_iops', 'xcol': 30, 'xname': 'DB IOPS'},
    {'ccol': 31, 'cname': 'db_physical_read_total_mbps', 'xcol': 31, 'xname': 'DB io read (mbps)'},
    {'ccol': 32, 'cname': 'db_physical_write_total_mbps', 'xcol': 32, 'xname': 'DB io write (mbps)'},
    {'ccol': 33, 'cname': 'db_physical_read_pct', 'xcol': 34, 'xname': 'DB io read (%)'},
    {'ccol': 34, 'cname': 'db_io_throughput_mbps', 'xcol': 33, 'xname': 'DB io throughput (mbps)'},

    # DB size data
    {'ccol': 35, 'cname': 'db_size_gb', 'xcol': 35, 'xname': 'DB (gb)'},
    {'ccol': 36, 'cname': 'db_tables_gb', 'xcol': 36, 'xname': 'Tables (gb)'},
    {'ccol': 37, 'cname': 'db_indexes_gb', 'xcol': 37, 'xname': 'Indexes (gb)'},

    # Others
    {'ccol': 38, 'cname': 'db_compatible', 'xcol': 38, 'xname': 'compatible'},
    {'ccol': 39, 'cname': 'db_optimizer_features_enable', 'xcol': 39, 'xname': 'optimizer_ features_ enable'},
    {'ccol': 40, 'cname': 'db_user_calls_ps', 'xcol': 40, 'xname': 'user calls (ps)'},
    {'ccol': 41, 'cname': 'db_user_commits_ps', 'xcol': 41, 'xname': 'user commits (ps)'},
    {'ccol': 42, 'cname': 'db_user_calls_pt', 'xcol': 42, 'xname': 'user calls (pt)'},
    {'ccol': 43, 'cname': 'db_user_commits_pt', 'xcol': 43, 'xname': 'user commits (pt)'},
    {'ccol': 44, 'cname': 'db_overfitting', 'xcol': 44, 'xname': 'Overfitting (calls / commits)'},
    {'ccol': 45, 'cname': 'elapsed_time_min', 'xcol': 45, 'xname': 'Elapsed Time (min)'},
    {'ccol': 46, 'cname': 'db_time_min',                'xcol': 46, 'xname': 'DB Time (min)'},
    {'ccol': 47, 'cname': 'db_avg_active_sessions',     'xcol': 47, 'xname': 'Avg Active Sessions'},
    {'ccol': 48, 'cname': 'db_cpu_pct_db_time', 'xcol': 48, 'xname': 'DB CPU (% DB Time)'},
    {'ccol': 49, 'cname': 'db_redo_mbps', 'xcol': 49, 'xname': 'Redo (mbps)'},
    {'ccol': 50, 'cname': 'db_net_bandwidth_mbitps', 'xcol': 50, 'xname': 'Net. Bandwidth (mbitps)'},
    {'ccol': 51, 'cname': 'db_log_file_sync_avg_wait_ms', 'xcol': 51, 'xname': 'log file sync avg wait (ms)'},
    {'ccol': 52, 'cname': 'db_log_file_pwrite_avg_wait_ms', 'xcol': 52, 'xname': 'log file parallel write avg wait (ms)'},
    {'ccol': 53, 'cname': 'db_table_scans_dread_total', 'xcol': 53, 'xname': 'table scans (direct read) total'},
    {'ccol': 54, 'cname': 'db_sql', 'xcol': 54, 'xname': 'SQL'},
    {'ccol': 55, 'cname': 'db_dbms', 'xcol': 55, 'xname': 'DBMS_Packages'},
    {'ccol': 56, 'cname': 'db_modules', 'xcol': 56, 'xname': 'Modules'},
    {'ccol': 57, 'cname': 'db_features', 'xcol': 57, 'xname': 'Oracle Features'},
    {'ccol': 58, 'cname': 'db_hints', 'xcol': 58, 'xname': 'Hints'},

    # RV Tool data
    {'ccol': 59, 'cname': 'esx_cpu_model', 'xcol': 59, 'xname': 'ESX CPU Model'},
    {'ccol': 60, 'cname': 'esx_cpu_speed', 'xcol': 60, 'xname': 'ESX CPU Speed'},
    {'ccol': 61, 'cname': 'esx_ht_available', 'xcol': 61, 'xname': 'ESX HT Available'},
    {'ccol': 62, 'cname': 'esx_ht_active', 'xcol': 62, 'xname': 'ESX HT Active'},
    {'ccol': 63, 'cname': 'esx_cpu_num', 'xcol': 63, 'xname': 'ESX CPUs'},
    {'ccol': 64, 'cname': 'esx_cores_per_cpu', 'xcol': 64, 'xname': 'ESX Cores per CPU'},
    {'ccol': 65, 'cname': 'esx_cores', 'xcol': 65, 'xname': 'ESX Cores'},
    {'ccol': 66, 'cname': 'esx_cpu_usage_pct', 'xcol': 66, 'xname': 'ESX CPU usage %'},
    {'ccol': 67, 'cname': 'esx_memory_mb', 'xcol': 67, 'xname': 'ESX Memory'},
    {'ccol': 68, 'cname': 'esx_memory_usage_pct', 'xcol': 68, 'xname': 'ESX Memory usage %'},
    # {'ccol': 69, 'cname': 'esx_vm_num', 'xcol': 69, 'xname': 'ESX VMs total'},
    # {'ccol': 70, 'cname': 'esx_vm_run', 'xcol': 70, 'xname': 'ESX VMs active'},
    # {'ccol': 71, 'cname': 'esx_vm_run_per_core', 'xcol': 71, 'xname': 'ESX VMs per core'},
    # {'ccol': 72, 'cname': 'esx_mem_usage_pct', 'xcol': 72, 'xname': 'ESX vCPUs total'},
    # {'ccol': 73, 'cname': 'esx_mem_usage_pct', 'xcol': 73, 'xname': 'ESX vCPUs per core'},
    # {'ccol': 74, 'cname': 'esx_mem_usage_pct', 'xcol': 74, 'xname': 'ESX vRAM alloc'},
    # {'ccol': 75, 'cname': 'esx_mem_vm_used', 'xcol': 75, 'xname': 'ESX vRAM used'},
    {'ccol': 69, 'cname': 'iops_per_sec_from_top_10_section', 'xcol': 69, 'xname': 'IOPS per sec from Top 10 section'},
    {'ccol': 70, 'cname': 'throughput_mb_per_sec_from_top_10_section', 'xcol': 70, 'xname': 'Throughput per sec from Top 10 section'},
]
"""
End of ConfigCsvArrays.py script
"""
"""
Begin of ConfigQueryArrays script used arrays configuraton for AWR analysis
"""

############ AWR Analysis Query Arrays #############

# Standard (Oracle single instance) queries for AWR html report analysis
# Queries form is [<lookup row>, <lookup column>, <csv column name>, {<datatype>, <decimal places>, <devisor>}]
# <datatype>       means 's' for string or 'n' for numeric (default: 's')
# <decimal places> number of decimal places for a numeric data type (default: 2)
#                  a value <= 0 -> integer data type
#                  a value > 0  -> float data type with defined number of decimal places (uses round_up function)
# <devisor>        means a numeric value division using the defined devisor eg. for byte to megabyte conversion
queries_STD = [
    # General
    ['', 'DB Id', 'db_id'],                              # report header section
    ['', 'DB Name', 'db_name'],                          # report header section
    ['', 'Unique Name', 'db_uname'],                     # report header section
    # some AWR versions e.g.12.1.0.2.0 doesn't provide a column 'Unique Name' in report header
    # so we are looking for a config parameter db_unique_name
    ['db_unique_name', 'Begin value', 'db_uname'],       # e.g. table "Initialization Parameters"
    ['', 'Instance', 'db_inst_name'],                    # report header section
    ['', 'Edition', 'db_edition'],                       # report header section
    ['', 'CDB', 'db_cdb'],                               # report header section
    ['', 'Release', 'db_release'],                       # report header section
    ['', 'Host Name', 'host_name'],                      # report header section
    ['', 'Platform', 'platform'],                        # report header section
    ['Begin Snap:', 'Snap Time', 'db_snap_begin_time'],  # report header section
    ['End Snap:', 'Snap Time', 'db_snap_end_time'],      # report header section

    # CPU capacity
    ['', 'CPUs', 'host_cpu_num', 'n'],                                  # report header section (host cpus) = CPU threads = Oracle CPUs
    ['cpu_count', 'Begin value', 'db_cpu_count', 'n'],                  # table "Initialization Parameters" > "Modified Parameters" = CPU threads = Oracle CPUs
    # CPU usage calculation
    ['BUSY_TIME', 'Value', 'host_cpu_busy_time_s', 'n', 2, 100],        # table "Operating System Statistics"
    ['IDLE_TIME', 'Value', 'host_cpu_idle_time_s', 'n', 2, 100],        # table "Operating System Statistics"
    ['DB CPU', 'Time \(s\)', 'db_cpu_fg_time_s', 'n', 2],               # table "Time Model Statistics"
    ['background cpu time', 'Time \(s\)', 'db_cpu_bg_time_s', 'n', 2],  # table "Time Model Statistics"
    # ['total CPU time', 'Time \(s\)', 'db_cpu_total_time_s', 'n', 2],  # table "Time Model Statistics" (not available in 10g reports)

    # Memory capacity
    ['Host Mem \(MB\):', 'Begin', 'host_memory_mb', 'n'],                        # table "Memory Statistics" (host memory)
    # Memory usage calulation
    ['SGA use \(MB\):', 'Begin', 'db_sga_usage_mb', 'n'],                        # table "Memory Statistics"
    ['PGA use \(MB\):', 'Begin', 'db_pga_usage_mb', 'n'],                        # table "Memory Statistics"
    # ['Total', 'Used \(MB\)', 'db_pga_usage_mb', 'n'],                          # table "Process Memory Summary" - have to be tested (row = B+Total)!
    # ['', 'Alloc \(MB\)', 'db_pga_usage_mb', 'n', 2],                           # table "Process Memory Summary" - have to be tested (row = B+Total)!
    # ['PGA Target:', 'Begin', 'db_pga_target_mb', 'n', 0, 1048576],             # table "Database Resource Limits"
    # ['SGA Target:', 'Begin', 'db_sga_target_mb', 'n', 0, 1048576],             # table "Database Resource Limits"
    # ['Memory Target', 'Begin', 'db_memory_target_mb', 'n', 0, 1048576],        # table "Database Resource Limits"
    # ['Memory Usage %:','End', 'db_shared_pool_usage_pct', 'n', 2],             # table "Shared Pool Statistics"
    # ['pga_aggregate_target', 'Begin value', 'db_pga_aggregate_target_mb', 'n', 0, 1048576],  # table "Initialization Parameters" > "Modified Parameters"
    # ['sga_max_size', 'Begin value', 'db_sga_max_size_mb', 'n', 0, 1048576],    # table "Initialization Parameters" > "Modified Parameters"
    # ['sga_target', 'Begin value', 'db_sga_target_mb', 'n', 0, 1048576],        # table "Initialization Parameters" > "Modified Parameters" - 0 means disabled sga components auto tuning
    # ['memory_target', 'Begin value', 'db_memory_target_mb', 'n', 0, 1048576],  # table "Initialization Parameters" > "Modified Parameters" - 0 means disabled sga and pga auto tuning

    # IO usage calulation
    ['physical read total IO requests','per Second', 'db_physical_read_total_io_ps', 'n', 2],       # table "Instance Activity Stats"
    ['physical write total IO requests', 'per Second', 'db_physical_write_total_io_ps', 'n', 2],    # table "Instance Activity Stats"
    ['physical read total bytes','per Second', 'db_physical_read_total_mbps', 'n', 2, 1048576],     # table "Instance Activity Stats"
    ['physical write total bytes', 'per Second', 'db_physical_write_total_mbps', 'n', 2, 1048576],  # table "Instance Activity Stats"

    # Workload
    ['user calls', 'per Second', 'db_user_calls_ps', 'n', 2],                                 # table "Report Summary" - Load Profile" or "Instance Activity Statistics" > "Key Instance Activity Stats" | "Instance Activity Stats" ???
    ['user commits', 'per Second', 'db_user_commits_ps', 'n', 2],                             # table "Instance Activity Statistics" > "Key Instance Activity Stats" | "Instance Activity Stats" ???
    ['user calls', 'per Trans', 'db_user_calls_pt', 'n', 2],                                  # table "Report Summary" - Load Profile" or "Instance Activity Statistics" > "Key Instance Activity Stats" | "Instance Activity Stats" ???
    ['user commits', 'per Trans', 'db_user_commits_pt', 'n', 2],                              # table "Instance Activity Statistics" > "Key Instance Activity Stats" | "Instance Activity Stats" ???
    ['Redo size \(bytes\):', 'Per Second', 'db_redo_mbps', 'n', 6, 1048576],                  # table "Report Summary" > "Load Profile"
    ['log file sync','Avg wait', 'db_log_file_sync_avg_wait_ms', 'n', 2],                     # table "Report Summary" > "Top 10 Foreground Events by Total Wait Time" or "Foreground Wait Events" or "Background Wait Events" !?
    ['log file sync','Avg wait \(ms\)', 'db_log_file_sync_avg_wait_ms', 'n', 2],              # 11.2.0.3.0, 11.2.0.4.0, 12.1.0.2.0 -> column name "Avg waits (ms)"
    ['log file parallel write', 'Avg wait', 'db_log_file_pwrite_avg_wait_ms', 'n', 2],        # table "Report Summary" > "Top 10 Foreground Events by Total Wait Time" or "Foreground Wait Events" or "Background Wait Events" !?
    ['log file parallel write','Avg wait \(ms\)', 'db_log_file_pwrite_avg_wait_ms', 'n', 2],  # 11.2.0.3.0, 11.2.0.4.0, 12.1.0.2.0 -> column name "Avg waits (ms)"
    ['table scans \(direct read\)', 'Total', 'db_table_scans_dread_total', 'n'],              # table "Instance Activity Stats"

    # Time values
    ['Elapsed:', 'Snap Time', 'elapsed_time_min', 'n', 2],                        # report header section
    ['DB Time:', 'Snap Time', 'db_time_min', 'n', 2],                             # report header section
    ['DB CPU', '% DB time', 'db_cpu_pct_db_time', 'n', 2],                        # table "Time Model Statistics"

    # Others
    ['compatible','Begin value', 'db_compatible'],                                # table "Initialization Parameters" > "Modified Parameters"
    ['optimizer_features_enable','Begin value', 'db_optimizer_features_enable'],  # table "Initialization Parameters" > "Modified Parameters"
]

# Oracle RAC related queries for AWR html report analysis
# Queries form is [<lookup row>, <lookup column>, <csv column name>, {<datatype>, <decimal places>, <devisor>}]
# <datatype>       means 's' for string or 'n' for numeric (default: 's')
# <decimal places> number of decimal places for a numeric data type (default: 2)
#                  a value <= 0 -> integer data type
#                  a value > 0  -> float data type with defined number of decimal places (uses round_up function)
# <devisor>        means a numeric value division using the defined devisor eg. for byte to megabyte conversion
queries_RAC=[
    # General
    ['', 'Id', 'db_id'],                            # table "Database Summary"
    ['', 'Name', 'db_name'],                        # table "Database Summary"
    ['', 'Unique Name', 'db_uname'],                # table "Database Summary" - not set in 12.1.0.2.0 but in 19.0.0.0.0!!!
    # # some AWR versions e.g. 12.1.0.2.0 doesn't provide a column 'Unique Name' in report header
    # # so we are looking for a config parameter db_unique_name
    # ['db_unique_name', 'Begin value', 'db_uname'],  # e.g. table "Supplemental Information" > "Init.ora Parameters"
    ['', 'Edition', 'db_edition'],                  # table "Database Summary"
    ['', 'CDB', 'db_cdb'],                          # table "Database Summary"

    # cpu - metrics are captured on instance level
    # memory - metrics are captured on instance level
    # io - metrics are captured on global level (not available at all on instance level)
    # io usage calulation
    ['physical read total IO requests','per Second', 'db_physical_read_total_io_ps', 'n', 2],       # table "System Statistics (Global)"
    ['physical write total IO requests', 'per Second', 'db_physical_write_total_io_ps', 'n', 2],    # table "System Statistics (Global)"
    ['physical read total bytes','per Second', 'db_physical_read_total_mbps', 'n', 2, 1048576],     # table "System Statistics (Global)"
    ['physical write total bytes', 'per Second', 'db_physical_write_total_mbps', 'n', 2, 1048576],  # table "System Statistics (Global)"

    # Workload
    ['user calls', 'per Second', 'db_user_calls_ps', 'n', 2],                           # table "System Statistics (Global)"
    ['user commits', 'per Second', 'db_user_commits_ps', 'n', 2],                       # table "System Statistics (Global)"
    ['user calls', 'per Trans', 'db_user_calls_pt', 'n', 2],                            # table "System Statistics (Global)"
    ['user commits', 'per Trans', 'db_user_commits_pt', 'n', 2],                        # table "System Statistics (Global)"
    ['redo size', 'per Second', 'db_redo_mbps', 'n', 6, 1048576],                       # table "System Statistics (Global)"
    ['table scans \(direct read\)', 'Total', 'db_table_scans_dread_total', 'n'],        # table "System Statistics (Global)"
    ['log file sync','Avg Wait', 'db_log_file_sync_avg_wait_ms', 'n', 2],               # table "Foreground Wait Events (Global)"; whats about "Background Wait Events (Global)" ?
    ['log file parallel write','Avg Wait', 'db_log_file_pwrite_avg_wait_ms', 'n', 2],   # table "Redo Write Histogram" | "Background|Foreground Wait Events (Global)" ?

    # Time values
    ['', 'Elapsed time', 'elapsed_time_min', 'n', 2],  # table "Database Summary"
    ['', 'DB time', 'db_time_min', 'n', 2],            # table "Database Summary"
]

# Oracle RAC instance specific queries for AWR html report analysis
# Queries form is [<lookup row>, <lookup column>, <csv column name>, {<datatype>, <decimal places>, <devisor>}]
# <lookup row>     value will be replaced by rac instance id if set to ''
# <datatype>       means 's' for string or 'n' for numeric (default: 's')
# <decimal places> number of decimal places for a numeric data type (default: 2)
#                  a value <= 0 -> integer data type
#                  a value > 0  -> float data type with defined number of decimal places (uses round_up function)
# <devisor>        means a numeric value division using the defined devisor eg. for byte to megabyte conversion
# This queries use the instance id for <lookup row> value. We do not have to define it here.
queries_RAC_Instance = [
    # General
    ['', 'Instance', 'db_inst_name'],                         # table "Database Instances Included In Report"
    ['', 'Release', 'db_release'],                            # table "Database Instances Included In Report"
    ['', 'Host', 'host_name'],                                # table "Database Instances Included In Report"
    ['', 'Platform', 'platform'],                             # table "Database Instances Included In Report"
    ['', 'Begin Snap Time', 'db_snap_begin_time'],            # table "Database Instances Included In Report"
    ['', 'End Snap Time', 'db_snap_end_time'],                # table "Database Instances Included In Report"

    # CPU capacity
    ['', '#CPUs', 'host_cpu_num', 'n'],                       # table "OS Statistics By Instance" (release 19.0.0.0.0)
    ['', 'Num CPUs', 'host_cpu_num', 'n'],                    # table "OS Statistics By Instance" (release 11.2.0.4.0)
    ['cpu_count', 'Begin value', 'db_cpu_count', 'n'],        # table "init.ora Parameter"
    # CPU usage calculation
    ['', 'Busy', 'host_cpu_busy_time_s', 'n', 2],             # table "OS Statistics By Instance"
    ['', 'Idle', 'host_cpu_idle_time_s', 'n', 2],             # table "OS Statistics By Instance"
    ['', 'DB CPU \(s\)', 'db_cpu_fg_time_s', 'n', 2],         # table "Time Model Statistics"
    ['', 'bg CPU \(s\)', 'db_cpu_bg_time_s', 'n', 2],         # table "Time Model Statistics"

    # Memory capacity
    ['', 'Memory \(M\)', 'host_memory_mb', 'n'],              # table "OS Statistics By Instance" (release 11.2.0.4.0; 12.1.0.2.0)
    ['', 'MB', 'host_memory_mb', 'n'],                        # table "OS Statistics By Instance" (release 18.0.0.0.0; 19.0.0.0.0)
    # Memory usage calulation
    # ['', 'PGA Target - Begin', 'db_pga_usage_mb', 'n'],                         # table "Report Summary - Cache Sizes"
    # ['', 'Sga Target - Begin', 'db_sga_usage_mb', 'n'],                         # table "Report Summary - Cache Sizes"
    # ['', 'DB Cache - Begin', 'db_cache_usage_mb', 'n'],                         # table "Report Summary - Cache Sizes"
    # ['', 'Shared Pool - Begin', 'db_shpool_usage_mb', 'n'],                     # table "Report Summary - Cache Sizes"
    # ['', 'Memory Target - Begin', 'host_memory_mb', 'n'],                       # table "Report Summary - Cache Sizes"
    # ['Total', 'Used \(MB\)', 'db_pga_usage_mb', 'n'],                           # table "Process Memory Summary" - have to be tested (row = I#+B+Total)!
    # ['', 'Alloc \(MB\)', 'db_pga_usage_mb', 'n', 2],                            # table "Process Memory Summary" - have to be tested (row = I#+B+Total)!
    ['pga_aggregate_target', 'Begin value', 'db_pga_usage_mb', 'n', 0, 1048576],  # table "init.ora Parameter"
    ['sga_max_size', 'Begin value', 'db_sga_usage_mb', 'n', 0, 1048576],          # table "init.ora Parameter"
    ['sga_target', 'Begin value', 'db_sga_usage_mb', 'n', 0, 1048576],            # table "init.ora Parameter"; 0 means disabled sga components auto tuning
    ['memory_target', 'Begin value', 'db_memory_mb', 'n', 0, 1048576],            # table "init.ora Parameter"; 0 means disabled sga and pga auto tuning

    # IO usage calulation
    # RAC instance based IO metrics are available in table "Global Activity Load Profile" > "System Statistics - Per Second"
    # - It doesn't support io request metrics
    # - IO throughput metrics are collected in blocks only ("Physical Reads/s" and "Physical Writes/s")
    # - You have to multiply the blocks with configured "db_block_size" value from "init.ora Parameters"
    # Therefore, we currently do not capture instance-based IO values.

    # Workload
    ['', 'Redo Size \(k\)/s', 'db_redo_mbps', 'n',6, 1024],                # table "System Statistics - Per Seconds"
    # AAS is not used here; calculated using db_time_min and elapsed_time_min
    # ['', 'Avg Active Sessions', 'db_avg_active_sessions', 'n', 2],      # table "Datbase Instance Included In Report"

    # Time values
    # Elapsed time and DB time are used here for instance level AAS calculation
    ['', 'Elapsed Time\(min\)', 'elapsed_time_min', 'n', 2],                      # table "Database Instance Included In Report"
    ['', 'DB time\(min\)', 'db_time_min', 'n', 2],                                # table "Database Instance Included In Report"
    ['', 'DB CPU', 'db_cpu_pct_db_time', 'n', 2],                                 # table "Time Model Statistics" > "Time Model - % of DB time"
    ['', 'DB CPU +%DB time', 'db_cpu_pct_db_time', 'n', 2],                        # table "Time Model Statistics" > "Time Model - % of DB time"  (release 12.1.0.2.0)

    # Others
    ['compatible','Begin value', 'db_compatible'],                                # table "init.ora Parameter"
    ['optimizer_features_enable','Begin value', 'db_optimizer_features_enable'],  # table "init.ora Parameter"
]

# RAC global level value calculations based on RAC instance level values
# [column,calc,decimalplaces]
# If you look for values copied from RAC global level to instance level,
# then look for 'Duplicate some values from global RAC level record to instance level records' in Main.py
instance_column_calculations = [
    # General
    # ['db_snap_begin_time', 'min'],  # maybe in a future release ?
    # ['db_snap_end_time', 'max'],    # maybe in a future release ?
    # ['db_release', 'min'],          # maybe in a future release ?
    # CPU
    ['host_cpu_num', 'sum', 0],
    ['db_cpu_count', 'sum', 0],
    # ['db_cpu_num', 'sum', 0],         # set by AddCalculations.py
    ['host_cpu_busy_time_s', 'sum', 2],
    ['host_cpu_idle_time_s', 'sum', 2],
    ['db_cpu_fg_time_s', 'sum', 2],
    ['db_cpu_bg_time_s', 'sum', 2],
    # Memory
    ['host_memory_mb', 'sum', 0],
    ['db_sga_usage_mb', 'sum', 0],
    ['db_pga_usage_mb', 'sum', 0],
    ['db_memory_mb', 'sum', 0],
    # Others
    # ['db_redo_mbps','sum', 2],       # db_redo_mbps is also fetched on global rac level
    ['elapsed_time_min', 'avg', 2],    # should be max but avg does the same if all instance values are available
    ['db_time_min', 'sum', 2],
    ['db_cpu_pct_db_time', 'avg', 2],
    # RVTools
    ['RV CPUs', 'sum', 0],
    ['RV Cores', 'sum', 0],
    ['RV CPU usage %','avg', 0],
    ['RV Memory','sum', 0],
    ['RV Memory usage %','avg', 0],
]
"""
End of ConfigQueryArrays.py script
"""
"""
Begin of ConfigSqlArrays script used arrays configuraton for SQL text analysis
"""

########### SQL Text Analysis Arrays ############

# search name = name of defined search (can be identical for different pattern search)
# search pattern = sql search pattern (string or regular expression allowed)
# search type = contains flags for search type configuration
# - i = case insensitive search (default)
# - s = case sensitive search
# - r = regular expression search

# [ search name, search pattern, search type ]
sql_pattern_search_text = [
    ['count*', 'count(*)'],
    ['distinct', 'distinct'],
    ['begin', 'begin'],
    ['select_max', 'select.*max', 'r'],
    ['select*', 'select *'],
    ['order_by', 'order by'],
]

# [ search name, search pattern, search type ]
sql_pattern_search_dbms = [
    ['DBMS', 'dbms'],
    ['DBMS_SCHEDULER', 'dbms_scheduler'],
    ['DBMS_SNAPSHOT', 'dbms_snapshot'],
    ['DBMS_LOCK_ALLOCATED', 'dbms_lock_allocated'],
    ['DBMS_AQ', 'dbms_aq'],
    ['DBMS_JAVA', 'dbms_java'],
    ['DBMS_MVIEW', 'dbms_mview'],
    ['DBMS_XDB', 'dbms_xdb'],
    ['DBMS_JSON', 'dbms_json'],
    ['DBMS_RANDOM', 'dbms_random'],
    ['DBMS_XML', 'dbms_xml'],
    ['DBMS_UTILITY', 'dbms_utility'],
    ['DBMS_NLE', 'dbms_nle'],
    ['DBMS_TF', 'dbms_tf'],
    ['DBMS_OUTPUT', 'dbms_output'],
    ['DBMS_JOB', 'dbms_job'],
    ['DBMS_ASSERT', 'dbms_assert'],
    ['DBMS_SQLTUNE', 'dbms_sqltune'],
    ['DBMS_XPLAN', 'dbms_xplan'],
]

# Pattern for module lookup are searched in "SQL Text"
# unless the sql report table supports a "SQL Module" column.
# [ search name, search pattern, search type ]
sql_pattern_search_modules = [
    ['ESRI', 'ESRI', 's'],
    ['ArcSOC', 'ArcSOC', 's'],
    ['arcserver', 'arcserver'],   # same as ArcSOC ?
    ['JDBC', 'module: jdbc thin client'],
    ['Python', 'python'],
    ['DBMS_SCHEDULER', 'dbms_scheduler'],
]

# Oracle documentation - single row functions
# https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/Single-Row-Functions.html
# [ search name, search pattern, search type ]
sql_pattern_search_features = [
    ['xml', 'xml[a-z]*\(', 'r'],
    ['corr', 'corr(\_[sk])*\(', 'r'],
    ['first_value', 'first_value('],
    ['stddev', 'stddev(\_pop|\_samp)*\(', 'r'],
    ['rank', 'rank('],  # matches also dense_rank
    ['variance', 'var(iance|\_pop|\_samp)+\(', 'r'],
    ['sysdate', 'sysdate'],
    ['to_timestamp', 'to_timestamp(\_tz)*\(', 'r'],
    ['to_lob', 'to_[c]*lob\(', 'r'],
    ['to_number', 'to_number('],
    ['cast', 'cast('],
    ['rownum', 'rownum'],
    ['rowid', 'rowid'],
    ['scn', 'to\_scn\(|scn\_to\_timestamp|ora\_rowscn', 'r'],
    # functions like user or uid are very unspecific
    # because it doesn't need a parantesis for function parameters
    ['user', '[ ,(]+user[ ,)]+', 'r'],
    ['userenv', 'userenv('],
    ['regexp', 'regexp_'],
    ['bfilename', 'bfilename('],
    ['coalesce', 'coalesce('],
    ['decode', 'decode('],
    ['nvl', 'nvl('],
]
"""
End of ConfigSQLArrays.py script
"""
"""
Begin of HelperFuncitons.py script for functions regarding beautiful soup (parsing)
"""
from math import ceil

############### Helper Functions ###############

def isNaN(num):
    ''' check parameter for nan/null value '''
    return num != num

def round_up(n, decimals=0):
    '''
    round up a numeric value
    see https://realpython.com/python-rounding/#rounding-up
    '''
    if isNaN(n):
        return n
    multiplier = 10 ** decimals
    result = ceil(n * multiplier) / multiplier
    if decimals < 1:
        return int(result)  # return int if decimal points doesn't exists
    return result

def string_to_float(input):
    '''
    transform anumeric value into a float value
    depends on an american language formated input value
    '''
    s = str(input).strip()
    if isNaN(input) or len(s) == 0:
        return float('nan')   # returns a NaN (NULL) value float because of float('') == 0
    if '.' in s:
      dp = s.split('.')[-1]
      dp = float(dp) / 10 ** len(dp)
      s = ''.join(s.split('.')[:-1])
    else:
      dp = 0
    if s:
      ip = int(s.replace(',', '').replace('.',''))
    else:
      ip = 0
    return ip + dp

def first_line_for_phrase(text, phrase):
    for (i, line) in enumerate(text):
        if phrase in line:
            return i
    return -1
"""
End of HelperFunctions.py script
"""
"""
Begin of SoapParsingFunctions.py script for functions regarding beautiful soup (html parsing)
"""
import re
# for BeautifulSoup see
# - https://beautiful-soup-4.readthedocs.io/en/latest/
# - https://www.crummy.com/software/BeautifulSoup/bs4/doc/
from bs4 import BeautifulSoup

#from HelperFunctions import *
#from LocalExecParams import *

##### Functions regarding html report parsing ####

def find_table(tables, row_name="", col_name=""):
    """ Find the table that contains the row that we are looking for """

    # print("row_name=" + row_name + "; col_name=" + col_name)  # for debugging
    for table in tables:
        if row_name == "" or table.find_all(string=re.compile(row_name)):
            # some awr seem to have broken html --> "bug fix" - skip this SQLs section globaly (should be debuged and skiped for special oracle releases only)!
            # AWR 10.2.0.3.0 reports doesn't have table attributes 'summary'!
            if table.has_attr('summary') and table.attrs['summary'].startswith('SQL ordered by Offload Eligible Bytes'):
                continue
            # Gives all tables contain column name
            if table.find_all(string=re.compile(col_name)) or col_name == "":
                # check correct column is there
                rows = table.find_all('tr')
                for row in rows:
                    data = row.find_all('th')
                    is_found = [True for elem in data if re.match(col_name, elem.text)]
                    # is_found = [True for elem in data if col_name.replace('\\', '') == elem.text]
                    if any(is_found):
                        return table
    return

def get_value(table, row_name='', col_name='', instid=0):
    """ Parse the table and get the value of column <col_name> and row <row_name> """

    # print('row_name:', row_name, 'col_name:', col_name) # for debugging
    # if row_name == 'log file parallel write':           # for debugging
    #     print(row_name)
    # if col_name == 'DB time\\(min\\)':                  # for debugging
    #     print(col_name)

    header = table.findChildren(['th'])
    rows = table.findChildren(['tr'])
    col_idx = -1

    # get the column index for lookup column
    for c, col in enumerate(header):
        # if col.string and re.search(col_name, col.string) and 'colspan' not in col.attrs: # ignore top level column names - only nested
        # if col.string and col.string == col_name.replace("\\","") and 'colspan' not in col.attrs: # ignore top level column names - only nested
        if col.string and re.match(col_name, col.string) and 'colspan' not in col.attrs: # ignore top level column names - only nested
            col_idx = c
            break

    # Fixing indexing for RAC files (substract top level columns)
    for i in enumerate(header):
        if 'colspan' in i[1].attrs:
            col_idx -= 1

    # Exit if column lookup failed
    if col_idx == -1:
        return ""

    # Special handling for initialization/init.ora parameter table for rac databases
    # rac parameter can be defined for all "*" or specified "<InstID>" instances
    #
    # AWR 10.2.0.3.0 reports doesn't have table attributes 'summary' -> have to be fixed soon!
    # look for first column name (first th.string) = 'Parameter Name' insteed of table attribute 'summary'!
    if instid > 0 and table.has_attr('summary') and re.search('.*init.* parameters.*', table.attrs['summary']):
        for row in rows:
            cells = row.findChildren('td')
            # if cells and cells[0].string == row_name.replace("\\","") and ( cells[1].string == '*' or cells[1].string == str(instid)):
            if cells and re.match(row_name, cells[0].string) and ( cells[1].string == '*' or cells[1].string == str(instid)):
                    return cells[col_idx].string
        return ""

    # All other table lookups
    for row in rows:
        # Check if the row we are looking for (name or empty) exists
        # looking for row value in first 3 columns and return col_idx column value
        cells = row.findChildren('td')
        if cells and (
          row_name == ''
          or (cells[0].string and re.match(row_name, cells[0].string))
          or (len(cells) > 1 and cells[1].string and re.match(row_name, cells[1].string))
          or (len(cells) > 2 and cells[2].string and re.match(row_name, cells[2].string))
        ):
            return cells[col_idx].string
    return ""

def get_info(tables, row_name, col_name, instid=0):
    """ get desired entry based on col/row name """

    if len(tables) > 0:
        # Find the table that contains the row that we are looking for
        table = find_table(tables, row_name, col_name)
    else:
        print("Did not find ANY tables!")
        return

    if table:
        # Parse the table and get the value of column <col_name> and row <row_name>
        resultval = get_value(table, row_name=row_name, col_name=col_name, instid=instid)
        if resultval != None:
            return resultval
        else:
            return ""
    else:
        print("Did not find a table with col_name \"%s\" and row_name \"%s\"!" % (col_name, row_name))
    return

def get_soup(fileText):
    """ load file and create parseable data structure """

    soup = BeautifulSoup(fileText, features="html.parser")
    # https://beautiful-soup-4.readthedocs.io/en/latest/index.html?highlight=BeautifulSoup#encodings
    # https://beautiful-soup-4.readthedocs.io/en/latest/index.html?highlight=BeautifulSoup#inconsistent-encodings
    # soup = BeautifulSoup(fileText, features="html.parser", from_encoding="iso-8859-8", exclude_encodings=["iso-8859-7"])
    return soup

def get_tables(soup):
    """ fetch all html tables from html soup """

    tables = soup.findChildren('table') # get all html tables
    return tables

def get_tables(soup, type = 'all'):
    """
    fetch all html tables from html soup
    you can limit the result set to specified subset ('report' or 'warning' tables)
    sometimes additional warnings related html tables are present in front of the 'WORKLOAD REPORISTORY REPORT'
    """
    if type != 'all':
        h1 = soup.find('h1', string=re.compile("WORKLOAD REPOSITORY .*REPORT", re.IGNORECASE))
        h1Sourceline = h1.sourceline
        h1Sourcepos = h1.sourcepos
    def awrTables(tag):
        # see this https://scrapeops.io/python-web-scraping-playbook/python-beautifulsoup-findall/
        # and this https://beautiful-soup-4.readthedocs.io/en/latest/index.html?highlight=find_all#a-function
        if type == 'report':
            return tag.name == "table" and tag.sourceline >= h1Sourceline and tag.sourcepos >= h1Sourcepos
        elif type == 'warning':
            return tag.name == "table" and tag.sourceline <= h1Sourceline and tag.sourcepos < h1Sourcepos
        else:
            return tag.name == "table"
    tables = soup.find_all(awrTables)   # get all awr report related html tables
    return tables

def get_inst_list(inst_soup_table):
    """ fetch all rac instance ids from database instances table """

    inst_rows = inst_soup_table.findChildren(['tr'])
    inst_arr = []
    for inst_row in inst_rows:
        inst_cells = inst_row.findChildren('td')
        if inst_cells:
            inst_arr.append(int(inst_cells[0].string))
    # print(inst_arr)
    return inst_arr
"""
End of SoapParsingFunctions.py script
"""
"""
Begin of AWRParsingFunctions.py script for functions regarding AWR html report analysis
"""
# from operator import concat
#from SoapParsingFunctions import *
#from ConfigQueryArrays import *
#from ConfigSqlArrays import *
#from RunSQL import *

### Functions for analysis of AWR html reports ###

# Entry point for AWR report parsing
# def run(awr_soup, queries, isRacReport):
def run(soup_tables, queries, isRacReport):
    '''Analyse beautified html content from one AWR report file'''

    inst_total = 1      # total number of instances
    # inst_report = 1     # number of instances in report
    inst_list = []
    result = []
    result_cols = []

    # Add instance id field to query list (>0 for rac instance queries; ==0 for non rac or rac global queries)
    for i in range(len(queries)):
        queries[i] = [0] + queries[i]

    # Add queries for each instance in case of AWR RAC report
    # Look for instance number in AWR report section 'Database Instances Included In Report'
    if isRacReport:
        # inst_report = int(get_info([soup_tables[0]], '', 'In Report')) # table "Database Summary" - "Number of Instances"."In Report"
        inst_total = int(get_info([soup_tables[0]], '', 'Total')) # table "Database Summary" - "Number of Instances"."Total"

        # Get RAC instance id list from "Database Instance Included InReport" table
        inst_list = get_inst_list(soup_tables[1])

        # for instance in range(1, instance_num + 1):
        for instance in inst_list:
            for val in queries_RAC_Instance:
                row = val[0]
                if len(row) == 0:   # set row == instance number if row has an empty value
                    row = str(instance)
                queries.append([instance,row]+val[1:])

    # Run queries on AWR report and beautified result output
    for query in queries:
        result_dtype = 's'        # string data type
        result_dplaces = 0        # default value for float data type decimal places
        result_devisor = 1        # default for numeric value devision
        lookup_inst = query[0]    # lookup instance id esp. used for instance specific init.ora parameter lookup
        lookup_row = query[1]     # lookup row ( == instance id for RAC instance specific information)
        lookup_col = query[2]     # lookup column
        result_col = query[3]     # result key name
                   # query[4]     # result data type 's' for string and 'n' for numeric
                   # query[5]     # result decimal places (<=0: integer; >0: float rounded up)
                   # query[6]     # result divisor for unit conversion eg. from bytes to megabytes

        # if result_col == 'host_memory_mb':  # for debugging
        #     print(query)

        # Run query only if data not fetched by a previous query!
        if not str(lookup_inst) + "_" + result_col in result_cols:
            # Run query on awr report
            info = get_info(soup_tables, lookup_row, lookup_col, lookup_inst)

            # Run post processing on awr query results
            info = fix_awr_values(lookup_row, lookup_col, info, result_col)

            # If the query fetched a result value:
            # -> Record result_col as already fetched (should not be queried again if multiple queries are defined for same result_col)
            # -> Beautify result output (set data type and unit calculations)
            if info:
                result_cols.append(str(lookup_inst) + "_" + result_col)
                if len(query) > 6:    # devisor is specified
                    result_devisor = query[6]
                if len(query) > 5:    # decimal places are specified
                    result_dplaces = query[5]
                if len(query) > 4:    # data type is specified
                    if query[4] == 'n': result_dtype = 'n'  # numeric data type (float or int)

                if result_dtype == 'n':
                    try:
                        info = round_up(string_to_float(info)/result_devisor,result_dplaces)
                    except:
                        print("Failed in string_to_float('%s') for %s. Fallback to string!" % (info, result_col))
                        info = str(info).strip()
                else:
                    info = str(info).strip()

                result.append([lookup_inst, lookup_row, lookup_col, info, result_col])
                # print([lookup_inst, lookup_row, lookup_col, info, result_col])  # for debugging only

    return result, inst_total, inst_list

def fix_awr_values(row, col, res, key):
    '''Run post processing and fixes on AWR query result string values'''
    if row and col and key and res:
      if ( row == 'DB Time:' or row == 'Elapsed:') and '(mins)' in res:
          res = res[:-7]

      if ((row == "log file sync" or row == "log file parallel write") and "ms" in res):
          res = res.replace('ms', '')
      if ((row == "log file sync" or row == "log file parallel write") and  "us" in res):
          res.replace("us", "")
          res = str(round_up(string_to_float(res.replace("us", "")) / 1000, 2))
    return res

def search_sql(soup, sqlSource = 'sqlOrdered'):
    '''
    SQL analysis lookup function
    Can fetch SQL texts from sqlSource
      sqlOrdered: fetch SQLs from 'SQL Statistics - Top N SQL ordered by *' tables
      sqlList: fetch SQLs from 'Complete List of SQL Text' tables
    '''

    if sqlSource == 'sqlOrdered':
        # SQLs fetched from 'SQL Statistics - Top N SQL ordered by *' report tables
        # Table summary is different defined:
        # RAC example:    SQL ordered by Elapsed Time (Global)
        # NonRAC example: This table displays top SQL by elapsed time
        sqlSectionSearch = 'SQL ordered by'
    else:
        # SQLs fetched from 'SQL Statistics - Complete List of SQL Text' report table
        sqlSectionSearch = 'Complete List of SQL Text'

    # sqlTextHash = initSqlResults(sql_pattern_search_text)
    # sqlDbmsHash = initSqlResults(sql_pattern_search_dbms)
    # sqlModulesHash = initSqlResults(sql_pattern_search_modules)
    # oraFeaturesHash = initSqlResults(sql_pattern_search_features)
    sqlTextHash = {}
    sqlDbmsHash = {}
    sqlModulesHash = {}
    oraFeaturesHash = {}
    oraHintsHash = {}

    '''
    AWR 10.2.0.3.0 reports doesn't have a table attribute 'summary'!
    So we switched SQL table identification
    from an all table search and table filter on summary attribute
        tables = soup.findChildren('table')
        re.search(sqlSectionSearch, table.attrs['summary'], re.IGNORECASE)
    to an indirect table search using arefs in 'SQL Statistics' list
        arefs = soup.find_all('a', string=re.compile(sqlSectionSearch))
    '''

    # Get all arefs from 'SQL Statistics' link list for specified search string
    arefs = soup.find_all('a', string=re.compile(sqlSectionSearch))
    # Walk through search result, jump to defined href and get next table for 'SQL Text' column analysis
    for aref in arefs:
        h = aref.attrs["href"].rpartition("#")[2]
        table = aref.find_next("a", attrs={"name": h}).find_next("table")

        # Parse "SQL Text"
        rows = table.find_all('tr')
        SecondLastColName = table.find_all('th')[-2].text
        moduleColExists = re.match("SQL Module", SecondLastColName, re.IGNORECASE)
        for row in rows:
            if len(row) != 0:
                # Search only in last td ("SQL Text")
                tds = row.find_all('td')
                if len(tds) != 0:
                    # get sql from last td
                    sql_data = tds[-1].text
                    # Non RAC reports offer a "SQL Module" column in "SQL orderd by" report tables
                    if moduleColExists:
                        module_data = tds[-2].text
                    else:
                        module_data = sql_data

                    analyzeSQL(sqlTextHash, sql_data, sql_pattern_search_text)
                    analyzeSQL(sqlDbmsHash, sql_data, sql_pattern_search_dbms)
                    analyzeSQL(sqlModulesHash, module_data, sql_pattern_search_modules)
                    analyzeSQL(oraFeaturesHash, sql_data, sql_pattern_search_features)
                    searchHints(oraHintsHash, sql_data)

    # getSqlResults can return values without or with count for example: USE_HASH(7)
    # for count set'count' otherwise set 'key' for second parameter
    SQLtext = getSqlResults(sqlTextHash, 'count')
    SQLdbms = getSqlResults(sqlDbmsHash, 'count')
    SQLmodule = getSqlResults(sqlModulesHash, 'count')
    oraFeature = getSqlResults(oraFeaturesHash, 'count')
    oraHints = getSqlResults(oraHintsHash, 'count')

    return SQLtext, SQLdbms, SQLmodule, oraFeature, oraHints
"""
End of AWRParsingFunctions.py script
"""
"""
Begin of RunAWR.py script for functions regarding AWR report analysis
"""
#from ConfigQueryArrays import *
#from SoapParsingFunctions import *
#from AWRParsingFunctions import *

def extract_top_10_io_requests_section(awrSoup, globalResDict):
    
    target_text = "Top Databases by IO Requests"
    target_element = awrSoup.find(string=target_text)

    if target_element:
        # Get the table tag following the target element
        table = target_element.find_next('table')
        io_requests = -1
        io_throughput_mb = -1
        if table:
            # Extract data from the table as needed
            rows = table.find_all('tr')
            for row in rows:
                columns = row.find_all('td')
                if len(columns) > 5 :
                    db_name = columns[0].text.strip()
                    if "*" in db_name:
                        io_requests = float(columns[4].text.replace(',', '').strip())
                        io_throughput_mb = float(columns[8].text.replace(',', '').strip())
        
        if io_requests == -1:
            print(f"No DB details in {target_text} section")
        else:
            globalResDict['iops_per_sec_from_top_10_section'] = io_requests
            globalResDict['throughput_mb_per_sec_from_top_10_section'] = io_throughput_mb   
    else:
        print(f"Target text '{target_text}' not found in the HTML file.")
    

############## AWR report analysis ###############

def run_AWR(awrSoup, gobalResDict, sqlSource):
    '''Run AWR report analysis'''

    instTotalNum = 0
    resDict = []
    instList = []
    isRacDB = False       # Oracle RAC database (vs. single instance database)
    isRacReport = False   # AWR RAC report

    awrHeadTitle = awrSoup.head.title.text
    print("Title: " + str(awrHeadTitle))

    # Identify a RAC Report
    # We should test this for "global" and "nonGlobal" RAC report !!!

    # # Looks for a string "(RAC)" in first 150 characters of html awr report
    # isRacReport = int(awrSoup.text.find('(RAC)', 0, 150)) != -1

    # Looks for a string "RAC" in html title tag
    # RAC reports include 'AWR RAC Report' in html title tag
    isRacReport = int(awrHeadTitle.find('RAC', 0, 150)) != -1

    if isRacReport:
        query = queries_RAC.copy()
    else:
        query = queries_STD.copy()

    # Get html tables from awr report
    # allTables = get_tables(awrSoup)                 # not used actually
    # warningTables = get_tables(awrSoup, 'warning')  # not used actually
    reportTables = get_tables(awrSoup, 'report')

    # Identify a RAC database
    # #RAC = get_info(get_tables(awrSoup), '', 'RAC')

    # Looks for value of RAC column in html table (should be found in first report html table)
    # It's nessessary to identify the table with database "summary information"
    # without using the table summary attribute or any table heading.
    # A table attribute "summary" or a table heading are sometimes not available in awr report.
    RAC = get_info([reportTables[0]], '', 'RAC') # look for RAC only in first html table (Database Summary)
    if RAC.strip().upper() == "YES":
        isRacDB = True

    if isRacDB:
        gobalResDict['db_rac'] = 'YES'
        gobalResDict['db_type'] = 'RAC'
    else:
        gobalResDict['db_rac'] = 'NO'
        gobalResDict['db_type'] = 'SI'

    # Set status FAILED if wrong report type was used
    if isRacDB and not isRacReport:
        # gobalResDict['status'] = '(Attention: NonRAC report for RAC database)'
        gobalResDict['status'] = 'FAILED (RAC database but no RAC report)'
        print('Attention: NonRAC report used for RAC database')
    elif not isRacDB and isRacReport:
        gobalResDict['status'] = 'FAILED (RAC report but no RAC database)'
        print('Attention: RAC report used for NonRAC database')

    # Check for unsupported PDB or root level AWR report
    isPDBlevelAWR = (
        int(awrSoup.text.find('(PDB snapshots)', 0, 150)) != -1 or
        int(awrSoup.text.find('(root snapshots)', 0, 150)) != -1
    )
    # Check for unsupported AWR diff report
    isDiffAWR = int(awrSoup.text.find('COMPARE PERIOD REPORT', 0, 150)) != -1

    if isPDBlevelAWR:
        gobalResDict['status'] = 'UNSUPPORTED (pdb or root level report)'
        print('Skip unsupported awr report format (pdb or root level report)')
    elif isDiffAWR:
        gobalResDict['status'] = 'UNSUPPORTED (diff report)'
        print('Skip unsupported awr report format (compare period report)')
    else:
        # Run report analysis
        # Rac awr report may report less than total available instances (check instList)
        resDict, instTotalNum, instList = run(reportTables, query, isRacReport)
        gobalResDict['db_inst_num'] = instTotalNum

        # Search for special SQLs
        SQLtext, SQLdbms, SQLmodule, oraFeature, oraHints = search_sql(awrSoup, sqlSource)
        gobalResDict['db_sql'] = SQLtext
        gobalResDict['db_dbms'] = SQLdbms
        gobalResDict['db_modules'] = SQLmodule
        gobalResDict['db_features'] = oraFeature
        gobalResDict['db_hints'] = oraHints
    
    extract_top_10_io_requests_section(awrSoup, globalResDict=gobalResDict)

    return resDict, isRacDB, isRacReport, instTotalNum, instList
"""
End of RunAWR.py script
"""
"""
Begin of RunLST.py script for functions regarding Statspack report analysis
"""
import re
#from SoapParsingFunctions import *
#from HelperFunctions import *
#from ConfigQueryArrays import *
#from ConfigSqlArrays import *
#from RunSQL import *

########### Statspack report analysis ############

def run_LST(fileText, filename):
    '''Entry point for statspack parsing (statspack level 7 output supported only)'''

    # RAC reports are currently not supported!

    output = {}
    # output['filename'] = filename.replace('\\', '/')
    fileText = fileText.split('\n')
    foundLogFileSync = False
    foundLogFilePara = False
    notAvailable = 'n.a.'
    # db_time_ps = None
    # db_cpu_time_ps = None

    # RAC currently not supported for statspack reports
    isRacDB = False; isRacReport = False; inst_num = 1; inst_list = []
    output['db_type'] = 'SI'

    # Get first and last line number for SQL analysys lookups
    # First line number > first 'SQL ordered by' line
    # Last line number < 'Instance Activity Stats' line
    sqlFirstLine = first_line_for_phrase(fileText, 'SQL ordered by')
    sqlLastLine = first_line_for_phrase(fileText, 'Instance Activity Stats')

    # sqlTextHash = initSqlResults(sql_pattern_search_text)
    # sqlDbmsHash = initSqlResults(sql_pattern_search_dbms)
    # sqlModulesHash = initSqlResults(sql_pattern_search_modules)
    # oraFeaturesHash = initSqlResults(sql_pattern_search_features)
    sqlTextHash = {}
    sqlDbmsHash = {}
    sqlModulesHash = {}
    oraFeaturesHash = {}
    oraHintsHash = {}

    # sqlTextHash = initSqlResults(sql_pattern_search_text)
    # sqlDbmsHash = initSqlResults(sql_pattern_search_dbms)
    # sqlModulesHash = initSqlResults(sql_pattern_search_modules)
    # oraFeaturesHash = initSqlResults(sql_pattern_search_features)
    sqlTextHash = {}
    sqlDbmsHash = {}
    sqlModulesHash = {}
    oraFeaturesHash = {}
    oraHintsHash = {}

    # sqlTextHash = initSqlResults(sql_pattern_search_text)
    # sqlDbmsHash = initSqlResults(sql_pattern_search_dbms)
    # sqlModulesHash = initSqlResults(sql_pattern_search_modules)
    # oraFeaturesHash = initSqlResults(sql_pattern_search_features)
    sqlTextHash = {}
    sqlDbmsHash = {}
    sqlModulesHash = {}
    oraFeaturesHash = {}
    oraHintsHash = {}

    # Information not available in statspack reports
    # Information not available in statspack report version < 10.0.0.0.0!
    output['host_cpu_num'] = notAvailable
    output['platform'] = notAvailable
    output['host_memory_mb'] = notAvailable
    # Information not available in statspack report version >= 10.0.0.0.0!
    output['db_name'] = notAvailable
    # Information generally not available in statspack reports
    # db unique name info not available!
    output['db_uname'] = notAvailable
    # edition info not available!
    output['db_edition'] = notAvailable
    # cdb info not available!
    output['db_cdb'] = notAvailable


    # parse all lines from statspack report
    found = 0
    for i, row in enumerate(fileText):
        if row == '':
            continue
        try:
            # -----------------------------------------------------------------
            # Basic database information
            # -----------------------------------------------------------------

            # Statspack release < 10.0.0.0 (begin)
            if all(x in row for x in ['DB Name', 'DB Id']):
                # first table in report, column "Release"
                val = re.split(r" {1,}", fileText[i+2])
                # column DB Id
                output['db_name'] = val[0].strip()
                # column DB Id
                output['db_id'] = val[1].strip()
                # column Instance
                output['db_inst_name'] = val[2].strip()
                # column "Inst Num"
                output['db_inst_num'] = string_to_float(val[3])
                # column "Release"
                output['db_release'] = val[4].strip()
                # column "RAC"
                output['db_rac'] = val[5].strip()
                output['host_name'] = val[6].strip()
            # Statspack release < 10.0.0.0 (end)

            # Statspack release >= 10.0.0.0 (begin)
            if all(x in row for x in ['Database', 'DB Id']):
                # table "Database" (first table in report)
                val = re.split(r" {1,}", fileText[i+2])
                # column DB Id
                output['db_id'] = val[1].strip()
                # column Instance
                output['db_inst_name'] = val[2].strip()
                # column "Inst Num"
                output['db_inst_num'] = string_to_float(val[3])
                # column "Release"
                output['db_release'] = val[6].strip()
                # column "RAC"
                output['db_rac'] = val[7].strip()
            # Statspack release >= 10.0.0.0 (end)

            # https://docs.oracle.com/cd/E52734_01/core/ASADM/release.htm#ASADM445
            # https://docs.oracle.com/en/database/oracle/oracle-database/12.2/upgrd/about-oracle-database-release-numbers.html#GUID-1E2F3945-C0EE-4EB2-A933-8D1862D8ECE2
            # dbReleaseRec = [ Major, Maintnance, Minor, Patch Set, Patch Set Update]
            dbReleaseRec = output['db_release'].split('.')

            # DB name (second try)
            if ( re.search('^db_name ',row)
            and (not 'db_name' in output or isNaN(output['db_name']) or output['db_name'] == notAvailable)):
                val = re.split(r" {2,}", row)
                output['db_name'] = val[1].strip()

            # Statspack release < 10.0.0.0
            # does not support host platform, cpu and memory information

            # Statspack release 10.2.0.5 (begin)
            # does not support host platform information
            if all(x in row for x in ['Host  Name']):
                val = re.split(r" {1,}", row)
                output['host_name'] = val[2].strip()
            if all(x in row for x in ['Num CPUs']):
                val = re.split(r" {1,}", row)
                output['host_cpu_num'] = string_to_float(val[5])
            # Statspack release 10.2.0.5 (end)

            if all(x in row for x in ['Host', 'Name', 'Platform']):
                val = re.split(r" {2,}", fileText[i+2])
                # table "Host", column "Name"
                output['host_name'] = val[1].strip()
                # table "Host", column "Platform"
                output['platform'] = val[2].strip()
                # table "Host", column "CPUs"
                output['host_cpu_num'] = string_to_float(val[3])

            if all(x in row for x in ['Snap Id', 'Snap Time']):
                # table "Snapshot", column "Snap Time"
                val = re.split(r" {1,}", fileText[i+2])
                output['db_snap_begin_time'] = val[3].strip() + " " + val[4].strip()
                val = re.split(r" {1,}", fileText[i+3])
                output['db_snap_end_time'] = val[4].strip() + " " + val[5].strip()

            # -----------------------------------------------------------------
            # CPU capacity and usage
            # -----------------------------------------------------------------

            # Host cpu count (host_cpu_num)
            # already captured from host table (see above)!

            # DB cpu count usage limit (Parameter cpu_count)
            if re.search('^cpu_count ',row):
                # table "init.ora Parameters", column "Begin value"
                val = re.split(r" {2,}", row)
                output['db_cpu_count'] = string_to_float(val[1])

            # --- switched from table "Instance CPU" to "OS Statistics"     ---
            # --- "Instance CPU" is not filled at all in version 10.2.0.5.0 ---

            # if all(x in row for x in ['Host: Busy CPU time (s):']):
            #     # "host_cpu_busy_time_s" from table "Instance CPU"
            #     val = re.split(r" {2,}", row)
            #     host_cpu_busy_time_s = string_to_float(val[2])
            #     output['host_cpu_busy_time_s'] = host_cpu_busy_time_s
            # if all(x in row for x in ['Host: Total time (s):']):
            #     # "host_cpu_total_time_s" from table "Instance CPU"
            #     val = re.split(r" {2,}", row)
            #     host_cpu_total_time_s = string_to_float(val[2])

            # Host cpu busy time in seconds
            if all(x in row for x in ['BUSY_TIME ']):
                # table "OS Statistics"
                val = re.split(r" {2,}", row)
                host_cpu_busy_time_s = string_to_float(val[1]) / 100
                output['host_cpu_busy_time_s'] = host_cpu_busy_time_s
            # Host cpu idle time in seconds
            if all(x in row for x in ['IDLE_TIME ']):
                # table "OS Statistics"
                val = re.split(r" {2,}", row)
                host_cpu_idle_time_s = string_to_float(val[1]) / 100
                output['host_cpu_idle_time_s'] = host_cpu_idle_time_s

            # DB foreground cpu time in seconds (used for db cpu usage calculation)
            if all(x in row for x in ['DB CPU ']):
                # table "Time Model System Stats", column "Time (s)"
                found += 1
                if found == 1:
                    val = re.split(r" {2,}", row)
                    output['db_cpu_fg_time_s'] = string_to_float(val[1])
                    output['db_cpu_pct_db_time'] = string_to_float(val[2])
            # DB background cpu time in seconds (used for db cpu usage calculation)
            if all(x in row for x in ['background cpu time ']):
                # table "Time Model System Stats", column "Time (s)"
                val = re.split(r" {2,}", row)
                output['db_cpu_bg_time_s'] = string_to_float(val[1])

            # -----------------------------------------------------------------
            # Memory capacity and usage
            # -----------------------------------------------------------------

            # Host memory in mb
            if all(x in row for x in ['Host Mem (MB):']):
                # table "Memory Statistics", column "Begin"
                val = re.split(r" {1,}", row)
                output['host_memory_mb'] = string_to_float(val[4])
            # SGA used in mb
            if all(x in row for x in ['SGA use (MB):']):
                # table "Memory Statistics", column "Begin"
                val = re.split(r" {1,}", row)
                output['db_sga_usage_mb'] = string_to_float(val[4])
            # PGA used in mb
            if all(x in row for x in ['PGA use (MB):']):
                # table "Memory Statistics", column "Begin"
                val = re.split(r" {1,}", row)
                output['db_pga_usage_mb'] = string_to_float(val[4])

            # -----------------------------------------------------------------
            # IO usage statistics
            # -----------------------------------------------------------------

            # Physical read io per seconds
            if all(x in row for x in ['physical read total IO requests']):
                # table "Instance Activity Stats", column "Per Second"
                val = re.split(r" {1,}", row)
                output['db_physical_read_total_io_ps'] = string_to_float(val[6])
            # Physical write io per seconds
            if all(x in row for x in ['physical write total IO requests']):
                # table "Instance Activity Stats", column "Per Second"
                val = re.split(r" {1,}", row)
                output['db_physical_write_total_io_ps'] = string_to_float(val[6])

            # if all(x in row for x in ['physical read total bytes']):
            #     # table "Instance Activity Stats", column "Per Second"
            #     val = re.split(r" {2,}", row)
            #     output['db_physical_read_total_mbps'] = \
            #         string_to_float(val[1]) / 1048576
            # if all(x in row for x in ['physical write total bytes']):
            #     # table "Instance Activity Stats", column "Per Second"
            #     val = re.split(r" {2,}", row)
            #     output['db_physical_write_total_mbps'] = \
            #         string_to_float(val[1]) / 1048576

            # Physical read blocks per seconds (used for mb calculation)
            if all(x in row for x in ['Physical reads:']):
                # table "Load Profile", column "Per Second"
                val = re.split(r" {2,}", row)
                db_physical_read_blocks = string_to_float(val[2])
            # Physical write blocks per seconds (used for mb calculation)
            if all(x in row for x in ['Physical writes:']):
                # table "Load Profile", column "Per Second"
                val = re.split(r" {2,}", row)
                db_physical_write_blocks = string_to_float(val[2])
            # DB block size (used for read/write mb calculation)
            if re.search('^db_block_size', row):
                # table "init.ora Parameters", calumn "Begin value"
                val = re.split(r" {2,}", row)
                db_block_size = string_to_float(val[1])

            # -----------------------------------------------------------------
            # Workload statistics
            # -----------------------------------------------------------------

            # User calls per seconds/transaction
            if all(x in row for x in ['User calls:']):
            # if all(x in row for x in ['^user calls']):
                # table "Instance Activity Stats"
                val = re.split(r" {1,}", row)
                output['db_user_calls_ps'] = string_to_float(val[3])    # column "per Second"
                output['db_user_calls_pt'] = string_to_float(val[4])    # column "per Trans"

            # User commits per seconds/transaction
            if all(x in row for x in ['user commits']):
                # table "Instance Activity Stats"
                val = re.split(r" {1,}", row)
                output['db_user_commits_ps'] = string_to_float(val[3])  # column "per Second"
                output['db_user_commits_pt'] = string_to_float(val[4])  # column "per Trans"

            # Redo size in mb
            # if all(x in row for x in ['redo size']):
            #     if "for direct writes" not in row:
            #         val = re.split(r" {1,}", row)
            #         output['Redo (bps)'] = string_to_float(val[2])
            if all(x in row for x in ['Redo size:']):
                # table "Load Profile", column "Per Second"
                val = re.split(r" {1,}", row)
                output['db_redo_mbps'] = string_to_float(val[3])/1048576

            # Log file sync wait event
            # [Foreground|Background|both] wait event - what's the right source?
            # Actualy the first match wins.
            if all(x in row for x in ['log file sync']):
                # table "[Foreground|Background|both] Wait Events", column "Waits"
                if foundLogFileSync == False:
                    val = re.split(r" {1,}", row)
                    output['db_log_file_sync_avg_wait_ms'] = string_to_float(val[6])
                    foundLogFileSync = True

            # Log file parallel write wait event
            # [Foreground|Background|both] wait event - what's the right source?
            # Actualy the first match wins.
            if all(x in row for x in ['log file parallel write']):
                # table "[Foreground|Background|both] Wait Events", column "Waits"
                if foundLogFilePara == False:
                    val = re.split(r" {1,}", row)
                    output['db_log_file_pwrite_avg_wait_ms'] = string_to_float(val[7])
                    foundLogFilePara = True

            # Table scans (direct read) count
            if all(x in row for x in ['table scans (direct read)']):
                # table "Instance Activity Stats", column "Total"
                val = re.split(r" {1,}", row)
                output['db_table_scans_dread_total'] = string_to_float(val[4])

            # -----------------------------------------------------------------
            # Time statistics
            # -----------------------------------------------------------------

            # Elapsed time
            # if all(x in row for x in ['Elapsed:', 'Av Act Sess:']):
            #     val = re.split(r" {1,}", fileText[i])
            #     # table "Snapshot", column "Snap Id"
            #     output['elapsed_time_min'] = string_to_float(val[val.index('Elapsed:') + 1])
            #     # AAS is calculated in run_globalCalculations!
            #     # table "Snapshot", column "Sessions"
            #     # output['db_avg_active_sessions'] = \
            #     #     string_to_float(val[val.index('Sess:') + 1])
            if all(x in row for x in ['Snap Id', 'Snap Time']):
                # table "Snapshot", column "Snap Time"
                val = re.split(r" {2,}", fileText[i+4])
                # remove '(mins)' from value before string_to_float conversion
                output['elapsed_time_min'] = string_to_float(val[val.index('Elapsed:') + 1].split(' ')[0])

            # DB time (available since release 11.1)
            if all(x in row for x in ['DB time:', 'DB CPU:']):
                # table "Snapshot", column "Snap Id"
                val = re.split(r" {1,}", fileText[i])
                output['db_time_min'] = string_to_float(val[val.index('time:') + 1].replace('#',''))
            if ( re.search('^DB time ', row)
            and (not 'db_time_min' in output or isNaN(output['db_time_min']) or output['db_name'] == notAvailable)):
                # table "Time Model System Stats", column "Time (s)"
                val = re.split(r" {2,}", fileText[i])
                output['db_time_min'] = string_to_float(val[1])/60

            # if all(x in row for x in ['DB time(s):']):
            #     # table "Load Profile", column "Per Seconds"
            #     val = re.split(r" {2,}", row)
            #     db_time_ps = string_to_float(val[2])
            # if all(x in row for x in ['DB CPU(s):']):
            #     # table "Load Profile", column "Per Seconds"
            #     val = re.split(r" {2,}", row)
            #     db_cpu_time_ps = string_to_float(val[2])

            # -----------------------------------------------------------------
            # Others
            # -----------------------------------------------------------------

            # init.ora Parameter: compatible
            if all(x in row for x in ['compatible']):
                # table "init.ora Parameters", calumn "Begin value"
                val = re.split(r" {1,}", row)
                output['db_compatible'] = val[1].strip()
            # init.ora Parameter: optimizer_features_enable
            if all(x in row for x in ['optimizer_features_enable']):
                # table "init.ora Parameters", calumn "Begin value"
                val = re.split(r" {1,}", row)
                output['db_optimizer_features_enable'] = val[1].strip()

            # SQLs keyword lookups
            # Only between first 'SQL ordered by' line and 'Instance Activity Stats' line
            if i > sqlFirstLine and i < sqlLastLine:
                analyzeSQL(sqlTextHash, row, sql_pattern_search_text)
                analyzeSQL(sqlDbmsHash, row, sql_pattern_search_dbms)
                analyzeSQL(sqlModulesHash, row, sql_pattern_search_modules)
                analyzeSQL(oraFeaturesHash, row, sql_pattern_search_features)
                searchHints(oraHintsHash, row)
        except:
            continue

    output['db_sql'] = getSqlResults(sqlTextHash, 'count')
    output['db_dbms'] = getSqlResults(sqlDbmsHash, 'keys')
    output['db_modules'] = getSqlResults(sqlModulesHash, 'keys')
    output['db_features'] = getSqlResults(oraFeaturesHash, 'keys')
    output['db_hints'] = getSqlResults(oraHintsHash, 'keys')

    # Some calculations
    lvars = locals()
    # if all(var in lvars for var in ('host_cpu_total_time_s', 'host_cpu_busy_time_s')):
    #     output['host_cpu_idle_time_s'] = \
    #         host_cpu_total_time_s - host_cpu_busy_time_s
    if all(var in lvars for var in ('db_physical_read_blocks', 'db_block_size')):
        output['db_physical_read_total_mbps'] = \
            db_physical_read_blocks * db_block_size / 1048576
    if all(var in lvars for var in ('db_physical_write_blocks', 'db_block_size')):
        output['db_physical_write_total_mbps'] = \
            db_physical_write_blocks * db_block_size / 1048576
    # if db_cpu_time_ps and db_time_ps
    #     output['db_cpu_pct_db_time'] = round_up(db_cpu_time_ps / db_time_ps * 100, 2)

    if output['db_rac'] == "YES":
        output['db_type'] = 'RAC'
        # isRacDB = True    # statspack rac analysis currently not supported
        output['status'] = 'PASSED (limited rac support)'
    else:
        output['status'] = 'PASSED'

    return output, isRacDB, isRacReport, inst_num, inst_list
"""
End of RunLST.py script
"""
"""
Begin of RunSQL.py script for functions regarding sql analysis
"""
import re

############## SQL text analysis ################

def initSqlResults(search_array = []):
    result_hash = {}
    for item in search_array:
        result_hash[item[0]] = 0
    return result_hash

def analyzeSQL(result_hash = {}, sql_text = '', search_array = []):
    '''Search pattern in sql text'''

    def updateHash(hash, value):
        if not value in result_hash:
            hash[value] = 1
        else:
            hash[value] += 1

    # run search for all defined pattern on sql text
    for item in search_array:
        pattern = item[1]
        flag = ''
        # get defined flags
        # 's' means case sensitive search
        # 'i' means case insensitive search
        # 'r' means regular expression search
        if len(item) > 2:
            flag = item[2]
        # set case insensitive search flag 'i' (default)
        if not 's' in flag and not 'i' in flag:
            flag = flag + 'i'
        # for case insensitive search
        if 'i' in flag:
            # set search text to lower case
            sql = sql_text.lower()
            # set pattern to lower case except for regexp patterns
            if not ('r' in flag):
                pattern = pattern.lower()
        else:
            sql = sql_text

        # for a regular expression search
        if 'r' in flag:
            # mind the case insensitive search flag
            if 'i' in flag:
                regex = re.compile(pattern, re.IGNORECASE)
            else:
                regex = re.compile(pattern)
            if regex.search(sql):
                updateHash(result_hash, item[0])
        # run a common pattern search otherwise
        # it looks for a string in a string
        else:
            if pattern in sql:
                updateHash(result_hash, item[0])

def getSqlResults(result_hash = {}, type = 'count'):
    '''
    type can be 'count' -> "<FoundPattern1>(<Count>) <FoundPattern2(<Count>).."
             or 'keys'  -> "<FoundPattern1> <FoundPattern2>.."
    '''
    out = ''
    arr = []
    if type == 'count':
        for key in sorted(result_hash.keys()):
            arr.append(key + '(' + str(result_hash[key]) + ')')
        out = ' '.join(arr)
    else:
        # sep = ', '
        for key in sorted(result_hash.keys()):
            if result_hash[key] > 0:
                arr.append(key)
        out = ' '.join(arr)
    return out

############## SQL hint analysis ################

def searchHints(result_hash = {}, sql_text = ''):
    # Lookup for Oracle Hints
    # See Oracle docu for more information to hints
    # https://docs.oracle.com/en/database/oracle/oracle-database/21/sqlrf/Comments.html#GUID-D316D545-89E2-4D54-977F-FC97815CD62E

    # lookup for a hint comment (starts with "--+")
    match = re.split('--\+', sql_text)
    result = ''
    if len(match) > 1:
        # '--+' found, lookup for comment end characters not needed
        result = match[1]
        # get first non-whitespace-string only because eol was removed from sql string
        result = re.search('\S+', result)[0]
    if not result:
        # lookup for a hint comment (starts with "/*+")
        match = re.split('\/\*\+', sql_text)
        if len(match) > 1:          # '/*+' found
            result = match[1]
            for i in ['\*\/', '\*']:
                # lookup for hint comment end ('*/' or '*' if sql was cut off behind '*' character)
                match = re.split(i, result)
                if len(match) > 1:  # '*/' found
                    result = match[0]
                    break
    if result:
        # Found a hint comment
        # Remove brackets and brackets content
        result = re.sub( '\([^)]*', '', result)
        # Remove closing brackets and numeric values
        result = re.sub( '\)|\d', '', result)
        # Get all hints into an array
        result = result.upper()
        result = re.findall( '\w+', result)
        if result:
            for hint in result:
                if not hint in result_hash:
                    result_hash[hint] = 1
                else:
                    result_hash[hint] += 1
"""
End of RunSQL.py script
"""
"""
Begin of RunRVT.py script for functions regarding RV Tools report analysis
"""
#from HelperFunctions import *
#from ConfigCsvArrays import *

############ RV Tools report analysis ############

def run_RVT(dict, dnsname, vInfo_csv, vHost_csv):
    '''Run RV Tools report mapping'''
    print("Map RV tools records using dns name: ", dnsname)

    rvInCols = []; rvOutCols = [];
    for i in rvHostCols:
      rvInCols.append(i[0])
      rvOutCols.append(i[1])

    # Lookup hostname from VMware virtual hosts and get ESX hostname
    # mpils: dnsname match should maybe done in lowercase and without domain?
    matched_line_Info = vInfo_csv[vInfo_csv['DNS Name'] == dnsname]
    if matched_line_Info.loc[:, 'Host'].empty:
      print("DNS name not found in RVTools_tabvInfo.csv.")
    else:
      host_name = matched_line_Info.loc[:, 'Host'].values[0]

      # Lookup ESX hostname from VMware physical hosts
      matched_line_Host = vHost_csv[vHost_csv['Host'] == host_name]
      if matched_line_Host.loc[:, rvInCols].empty:
        print("Host not found in RVTools_tabvHost.csv.")
      else:
        data = matched_line_Host.loc[:, rvInCols]

        print(data)
        if data is not None:
            for i, col in enumerate(rvOutCols):
                value = data.iloc[:, i].values[0]
                # print(value)
                dict[col] = value
"""
End of RunRVT.py script
"""
"""
Begin of RunDBS.py script for functions regarding database size reporting
"""
import pandas

############### Database size csv mapping ###############

def run_DBS(dict, df, SelCols, OutCols):
    '''Run database size csv mapping'''

    # databases are mapped using DB name and DB unique name
    # DB unique name not filled in all AWRs!
    # DB name and db unique name not filled in Statspack reports!
    matched_line_db = pandas.DataFrame()
    if 'db_name' in dict:
        if 'db_uname' in dict:
            matched_line_db = df.loc[(df['DB_NAME'].str.lower() == dict['db_name'].lower()) & (df['DB_UNAME'].str.lower() == dict['db_uname'].lower()),SelCols]
        else:
            matched_line_db = df.loc[(df['DB_NAME'].str.lower() == dict['db_name'].lower()), SelCols]
    if matched_line_db.empty:
        print("Database not found in *-dbSize.csv files.")
    else:
      data_rec = matched_line_db.set_axis(OutCols, axis='columns').to_dict('records')  # -> [{}]
      dict.update(data_rec[0])     # only first matched database record used!
"""
End of RunDBS.py script
"""
"""
Begin of AddCalculations.py script for functions regarding report analysis post calculations
"""
#from HelperFunctions import *
#from ConfigQueryArrays import *

def calc_dbCpuUsage(res_dict, default=''):
    '''
    Database cpu usage calculation
    Calculation is based on available CPUs and database cpu usage rate
    '''
    db_cpus = default
    db_cpu_usage_pct = default
    if (    'host_cpu_num' in res_dict
        and 'host_cpu_busy_time_s' in res_dict
        and 'host_cpu_idle_time_s' in res_dict
        and 'db_cpu_fg_time_s' in res_dict
        and 'db_cpu_bg_time_s' in res_dict
    ):
        # cpu usage rate = total database cpu time / total host cpu time
        # cpu usage rate = (database foreground + background processes) / busy time + idle time
        total_host_cpu_time_s =   res_dict['host_cpu_busy_time_s'] + res_dict['host_cpu_idle_time_s']
        if total_host_cpu_time_s > 0:
            db_cpu_usage_rate = (res_dict['db_cpu_fg_time_s'] + res_dict['db_cpu_bg_time_s']) / total_host_cpu_time_s
            db_cpus = int(round_up(res_dict['host_cpu_num'] * db_cpu_usage_rate))
            db_cpu_usage_pct = round_up(db_cpu_usage_rate*100, 2)
            # ? should cpu usage percent be based on real cpu time usage or calculated db_cpus ?
            # db_cpu_usage_pct = round_up(db_cpus/res_dict['host_cpu_num']*100, 2)
    res_dict['db_cpu_num'] = db_cpus
    res_dict['db_cpu_usage_pct'] = db_cpu_usage_pct

def calc_dbMemoryUsage(res_dict, default=''):
    '''
    Database memory usage calculation
    Calculation is based on SGA and PGA values
    '''
    db_memory = default
    db_memory_pct = default
    if not 'db_memory_mb' in res_dict:
        if 'db_sga_usage_mb' in res_dict and isinstance(res_dict['db_sga_usage_mb'], (int, float)) and 'db_pga_usage_mb' in res_dict and isinstance(res_dict['db_pga_usage_mb'], (int, float)):
            db_memory = int(round_up(res_dict['db_sga_usage_mb'] + res_dict['db_pga_usage_mb']))
    else:
        db_memory = int(round_up(res_dict['db_memory_mb']))
    if isinstance(db_memory, (int, float)) and 'host_memory_mb' in res_dict and isinstance(res_dict['host_memory_mb'], (int, float)) and res_dict['host_memory_mb'] > 0:
        db_memory_pct = round_up(db_memory / res_dict['host_memory_mb'] * 100, 2)
    res_dict['db_memory_mb'] = db_memory
    res_dict['db_memory_usage_pct'] = db_memory_pct

def calc_dbIoUsage(res_dict, default=''):
    '''
    Database io calculation (IOPS, MBps, read MBps % from total io MBps)
    Read to Write Factor (read MBps % from total io MBps) used for workload io type classification
    '''
    db_iops = default
    db_io_throughput_mbps = default
    if 'db_physical_read_total_io_ps' in res_dict and 'db_physical_write_total_io_ps' in res_dict:
        db_iops = round(res_dict['db_physical_read_total_io_ps'] + res_dict['db_physical_write_total_io_ps'], 2)
    if 'db_physical_read_total_mbps' in res_dict and 'db_physical_write_total_mbps' in res_dict:
        db_io_throughput_mbps = round_up(res_dict['db_physical_read_total_mbps'] + res_dict['db_physical_write_total_mbps'], 2)
    res_dict['db_iops'] = db_iops
    res_dict['db_io_throughput_mbps'] = db_io_throughput_mbps

    readPct = default
    if 'db_physical_read_total_mbps' in res_dict and 'db_physical_write_total_mbps' in res_dict:
        read = res_dict['db_physical_read_total_mbps']
        write = res_dict['db_physical_write_total_mbps']
        if (read + write) > 0:
            readPct = round( (read / (read + write) * 100 ), 2)
    res_dict['db_physical_read_pct'] = readPct

def calc_dbNetBandwidthReq(res_dict, default=''):
    '''
    Oracle DataGuard required network bandwidth calculation based on redo log generation workload
    Calculation can be used esp. for Oracle DataGuard to Azure VM (Lift and Shift) migrations
    Result value unit is MBitPerSeconds
    '''
    db_net_bandwidth_mbitps = default
    if 'db_redo_mbps' in res_dict:
        db_net_bandwidth_mbitps = round(res_dict['db_redo_mbps'] / 0.75 * 8, 2)
    res_dict['db_net_bandwidth_mbitps'] = db_net_bandwidth_mbitps

def calc_dbAvgActiveSessions(res_dict, default=''):
    '''
    Calculate Average Active Sessions
    = Avarage amount of sessions running active on db
    = DB Time / Elapsed Time
    = "time of all active db sessions" / "Clock time"
    '''
    db_avg_active_sessions = default
    if 'db_time_min' in res_dict and 'elapsed_time_min' in res_dict and res_dict['elapsed_time_min'] > 0:
        db_avg_active_sessions = round(res_dict['db_time_min'] / res_dict['elapsed_time_min'], 2)
    res_dict['db_avg_active_sessions'] = db_avg_active_sessions

def calc_Overfitting(res_dict, default=''):
    '''
    Overfitting = % user calls to user commits
    Should be greater than 25 or 30 calls per commit
    Using calls/commits per transaction here because user calls are reported as 0 sometimes but transactions greate than 0
    '''
    db_overfitting = default
    if 'db_user_calls_pt' in res_dict and 'db_user_commits_pt' in res_dict and res_dict['db_user_commits_pt'] > 0:
        db_overfitting = round_up(res_dict['db_user_calls_pt'] / res_dict['db_user_commits_pt'], 2)
    res_dict['db_overfitting'] = db_overfitting

def run_instanceCalculations(racinst_res_dict):
    '''
    Some instance values are calculated based on other instance values
    racinst_res_dict = dict for RAC instances entries
    '''
    if len(racinst_res_dict) == 0:
        return
    for inst_dict in racinst_res_dict:
      calc_dbCpuUsage(inst_dict)          #, 'n.a.')
      calc_dbMemoryUsage(inst_dict)       #, 'n.a.')
      calc_dbNetBandwidthReq(inst_dict)   #, 'n.a.')
      calc_dbIoUsage(inst_dict)           #, 'n.a.')
      calc_dbAvgActiveSessions(inst_dict) #, 'n.a.')

def run_globalCalculations(global_res_dict, racinst_res_dict):
    '''
    Some calculations based on values already avalable from report analysis
    global_res_dict = dict for entries of Singe Instances (NonRac) or RAC global level
    racinst_res_dict = dict for entries of RAC instances
    '''
    # Calculate RAC global values based on instance values
    if len(racinst_res_dict) > 0:
        for col in instance_column_calculations:
            # if col[0] == 'db_id':  # for debugging
            #     print(col[0])
            cnt = 0; sum = 0; avg = 0; colFound = False; valValid = True

            # summarize instance values
            for instance in racinst_res_dict:
                # print('instance='+ str(instance)) # for debugging
                # message = 'instance: ' + str(instance['db_inst_id']) + ' column: ' + str(col) # for debugging
                if col[0] in instance and valValid:  # check if column exist in dict
                    # message = 'instance: ' + str(instance['db_inst_id']) + ' column: ' + str(col) + ' value: ' + str(instance[col[0]]) # for debugging
                    # print(message)  # for debugging
                    colFound = True
                    cnt += 1
                    if col[0] == 'n.a.' or isNaN(string_to_float(instance[col[0]])):
                        valValid = False
                        sum = 0
                        break
                    sum += instance[col[0]]
                # print(message)  # for debugging

            # global value aggregation (sum or avg)
            if colFound and valValid:
                if col[1] == 'sum':
                    sum = round_up(sum,col[2])
                    if col[2] == 0: sum = int(sum)
                    # global_res_dict[col[0]] = str(sum)
                    global_res_dict[col[0]] = sum
                else:
                    # avg = sum / len(racinst_res_dict)
                    avg = sum / cnt
                    avg = round_up(avg,col[2])
                    if col[2] == 0: avg = int(avg)
                    # global_res_dict[col[0]] = str(avg)
                    global_res_dict[col[0]] = avg

    # Calcualte NonRAC and RAC global values based on other global values
    calc_dbCpuUsage(global_res_dict, 'n.a.')
    calc_dbMemoryUsage(global_res_dict, 'n.a.')
    calc_dbIoUsage(global_res_dict, 'n.a.')
    calc_dbNetBandwidthReq(global_res_dict, 'n.a.')
    calc_Overfitting(global_res_dict, 'n.a.')
    calc_dbAvgActiveSessions(global_res_dict, 'n.a.')
"""
End of AddCalculations.py script
"""
"""
Begin of Main.py script used to parse data from AWR or Statspack Oracle db reports.
Can run locally or on JS --> change in "params" section

Input: (supported report types and other input files):
    - AWR Basic (.html)
    - AWR RAC (.html)
    - Statspack Level 7 (.lst)
    - DB Size (.csv)
    - RV Tools (.csv)

Ouput: Excel, CSV and JS pass with data from "sorted_output_columns" list

Requirements: pandas, beautifulsoup4, os, re, io, traceback
"""
################### Main Code ####################

import os, traceback
from io import StringIO
import re
import pandas # see https://pandas.pydata.org/docs/
from functools import reduce

#from LocalExecParams import *
#from ConfigCsvArrays import *
#from RunRVT import *
#from RunDBS import *
#from RunAWR import *
#from RunLST import *
#from AddCalculations import *

########## Some basic checks and initializations ##########

# Variables fileNames and fileTexts are passed by the calling module
# Check if files exists
if len(fileTexts) == 0:
    print("Could not find any files!")
    raise ValueError ("Could not find any files!")

if debug:
    print('Files: ',fileNames)  # array of names of all provided files
    # print(fileTexts)          # array of content of all provided files

# Some initializations
vHost = -1    # RVTools_tabvHost.csv content
vInfo = -1    # RVTools_tabvInfo.csv content
dbSize = -1   # *-dbSize.csv content
repCount = 0  # amount of uploaded and supported report files
if not 'sqlSource' in vars(): sqlSource = 'sqlOrdered'
# if not 'sqlSource' in vars(): sqlSource = 'sqlList'

all_dfs = []
dbSize_df = pandas.DataFrame()
dbInCols = []; dbOutCols = []; dbSelCols = []

# Get CSV column to XLS column mapping
csv2xsl = reduce(
  lambda o, i: o.update({i["cname"]: i["xname"]}) or o,
  # sorted(output_columns, key=lambda x: x["ccol"]),
  output_columns,
  {}
)
# Get CSV columns sorted in CSV column order
csvSortedCsvCols = reduce(
    lambda o, i: o.append(i["cname"]) or o,
    sorted(output_columns, key=lambda x: x["ccol"]),
    []
)
# Get CSV columns sorted in XLS column order
xlsSortedCsvCols = reduce(
    lambda o, i: o.append(i["cname"]) or o,
    sorted(output_columns, key=lambda x: x["xcol"]),
    []
)
# Get XLS columns sorted in XLS column order
xlsSortedXlsCols = reduce(
    lambda o, i: o.append(i["xname"]) or o,
    sorted(output_columns, key=lambda x: x["xcol"]),
    []
)
# Get selection and output columns for dbsize.csv file processing
for i in dbSizeCols:
    dbInCols.append(i[0])
    if i[1]:
        dbSelCols.append(i[0])
        dbOutCols.append(i[1])

############# Get special file data if exists #############

for count, fileText in enumerate(fileTexts):
    # Using pandas: https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html?highlight=read_csv#pandas.read_csv

    ###### Get RV tools csv data if exists ######

    # only one RVTools_tabvHost.csv file supported
    if fileNames[count] == "RVTools_tabvHost.csv" :
        vHost = fileTexts[count] # read RVTools_tabvHost.csv content from fileTexts array
        print("Found vHost file", fileNames[count])
        vHost_csv = pandas.read_csv(StringIO(vHost), lineterminator='\n', sep=';', skip_blank_lines=True)  # removed dtype='str'
        continue

    # only one RVTools_tabvInfo.csv file supported
    if fileNames[count] == "RVTools_tabvInfo.csv":
        vInfo = fileTexts[count] # read RVTools_tabvInfo.csv content from fileTexts array
        print("Found vInfo file", fileNames[count])
        vInfo_csv = pandas.read_csv(StringIO(vInfo), lineterminator='\n', sep=';', skip_blank_lines=True)  # removed dtype='str'
        continue

    #### Get database size csv data if exists ###

    # multiple *-dbSize.csv files supported
    if re.match(".*-dbSize.csv$", fileNames[count]):
        print("Found dbSize file", fileNames[count])
        dbSize = fileTexts[count]
        try:
            dbSize_csv = pandas.read_csv(StringIO(dbSize), lineterminator='\n', sep=';', skip_blank_lines=True, usecols=dbInCols)[dbInCols]  # used [dbInCols] to preserve column order
        except:
            print(traceback.format_exc())
        # Concat data from all *-dbsize.csv files into one dbSize dataframe object
        dbSize_df = pandas.concat([dbSize_df, dbSize_csv], ignore_index=True)
        continue

    #### Print message for unsupported files ###

    # Only AWR html files and Statspack lst files are suppoted, except for the other files processed above
    if not fileNames[count].lower().endswith(('.lst', '.html')):
        print('Skip unsupported file', fileNames[count])
        continue

    # increment the supported report files count
    repCount += 1

if repCount < 1:
    raise ValueError ("Could not find any supported report files!")

###### Run AWR/Statspack report analysis and data mapping from special files #####

# loop over every uploaded file content
# except for spezial files and unsupported files
for count, fileText in enumerate(fileTexts):
    try:
        # print('fileNames[count]', fileNames[count])

        # Only parse AWR '*.html' files and Statspack '*.lst' files
        if not fileNames[count].lower().endswith(('.lst', '.html')):
            continue

        # Some initializations
        print('--------------------------------------------------------------------------------')
        print('Parse file', fileNames[count])
        is_lst = fileNames[count][-4:] == ".lst" # current file is a Statspack output file
        global_res_dict = {}
        global_res_dict['filename'] = fileNames[count].replace('\\', '/')
        global_res_dict['parent'] = 'none'
        global_res_dict['status'] = ''

        # Run report analysis
        if is_lst:
            # Analyze NonRAC STATSPACK report
            # RAC reports are currently not supported
            lst_res, is_rac_db, is_rac_report, inst_total_num, inst_list = run_LST(fileText, fileNames[count])

            # convert lst_res into common used res_dict for post analysis process steps
            # actually only NonRAC supported for statspack reports
            res_dict = []
            keys = lst_res.keys()
            for key in keys:
              res_dict.append([0, '', '', lst_res[key], key])
        else:
            # Analyze RAC or NonRAC AWR report
            # Parse html tables into a json formated text
            awr_soup = get_soup(fileText)
            # if debug:
            #     print('- awr_soup.original_encoding -')
            #     print('Detected encoding for file "' + str(fileNames[count]) + '": ',awr_soup.original_encoding)

            # Run awr report analysis
            res_dict, is_rac_db, is_rac_report, inst_total_num, inst_list = run_AWR(awr_soup, global_res_dict, sqlSource)

        # Skip further processing for unsupported Statspack or AWR report formats
        if re.search('UNSUPPORTED', global_res_dict['status']):
            all_dfs.append(global_res_dict)
            continue

        ##### Report analysis result post processing #####

        if not is_rac_db:
            global_res_dict['db_inst_id'] = 1

        # for local debugging
        if local_dev and debug:
            print('---------- res_dict ----------')
            print(res_dict)
            f = open(os.path.join(outFolder, 'res_dict.json'), 'w')
            f.write(str(res_dict).replace("'", '"'))

            print('------ global_res_dict -------')
            print(global_res_dict)
            f = open(os.path.join(outFolder, 'global_res_dict.json'), 'w')
            f.write(str(global_res_dict).replace("'", '"'))

        # Prepare RAC instance records
        # Create dict for all RAC instance results
        # New CSV line for each RAC instance
        inst_res_dict = []
        inst_range = range(1, inst_total_num + 1)
        inst_range_list = [x for x in list(inst_range)]

        # Push basic values for RAC instances into RAC instance dictionaries
        if is_rac_report:
            for instance in inst_range:
                inst_res_dict.append({})
                inst_res_dict[instance - 1]['status']     = ''
                inst_res_dict[instance - 1]['db_inst_id'] = instance
                inst_res_dict[instance - 1]['db_type']    = 'RACI'
                inst_res_dict[instance - 1]['filename']   = fileNames[count].replace('\\', '/')
                inst_res_dict[instance - 1]['parent']     = fileNames[count].replace('\\', '/')
                inst_res_dict[instance - 1]['db_rac']     =  global_res_dict['db_rac']  # copy from RAC global dict

        # Add global values (SI|RAC) to global record and instance values (RAC) to instance records
        for entry in res_dict:
            # each entry contains [lookup-row, lookup-column, lookup-result-value, result-key-name]
            inst = entry[0]
            row = entry[1]
            col = entry[2]
            res = entry[3]
            key = entry[4]

            if is_rac_report and inst in inst_range_list:
                '''Push key/value to instance record (RAC) specific dict'''
                inst_res_dict[inst - 1][key] = res
            else:
                # NonRAC or RAC with only one instance
                '''Push key/value to the global record (SI|RAC)'''
                global_res_dict[key] = res

            # Duplicate some values from global RAC level record to instance RAC level records
            matches = ['db_name', 'db_uname', 'db_edition', 'db_cdb','db_id']
            if key in matches and inst_total_num > 1:
                for instance in inst_range:
                    inst_res_dict[instance - 1][key] =  res

        # Set status to PASSED if not set already (not UNSUPPORTED or FAILED)
        if len(global_res_dict['status']) == 0:
            global_res_dict['status'] = 'PASSED'
        # global_res_dict['status'] = ('PASSED ' + global_res_dict['status'].strip())
        if is_rac_report:
            for instance in inst_range:
                if len(inst_res_dict[instance - 1]['status']) == 0:
                    if instance in inst_list:
                        inst_res_dict[instance - 1]['status'] = 'PASSED'
                    else:
                        inst_res_dict[instance - 1]['status'] = 'FAILED (not in report)'
                # if instance in inst_list:
                #     inst_res_dict[instance - 1]['status'] = ('PASSED ' + inst_res_dict[instance - 1]['status'].strip())
                # else:
                #     inst_res_dict[instance - 1]['status'] = 'FAILED (not in report)'

        ############### Map RV Tools data ################

        if vInfo != -1 and vHost != -1:
            # RVTools data mapping based on hostname
            try:
                # for AWR RAC reports only
                if is_rac_report:
                    '''
                    Check RAC instance level using inst_res_dict
                    Each RAC instance has an own record in inst_res_dict
                    RVTools content have to be mapped to each instance record
                    '''
                    for inst in inst_res_dict:
                        run_RVT(instance, inst['host_name'], vInfo_csv, vHost_csv)

                # for AWR NonRAC reports
                else:
                    '''Check global level using global_res_dict'''
                    run_RVT(global_res_dict, global_res_dict['host_name'], vInfo_csv, vHost_csv)
            except:
                print(traceback.format_exc())

        ############# Map database size data #############

        # DB size data mapping based on dbname and dbuname
        # only for global_res_dict not for instances !
        if dbSize != -1:
            # Some or all? statspack reports doesn't support database name 'db_name'
            # So we can not map db size information for this reports.
            try:
                run_DBS(global_res_dict, dbSize_df, dbSelCols, dbOutCols)
            except:
                print(traceback.format_exc())

        ######### Reduce single instance RAC dict ########

        # If only one RAC instance available
        # Copy values from RAC instance dict to RAC global dict
        # and clear instance dict
        if is_rac_report and len(inst_res_dict) == 1:
            instance = inst_res_dict[0]
            for key in instance:
                # print('key: ', key)   # for debugging only
                if key not in ['filename', 'parent', 'db_type', 'status']:
                    global_res_dict[key] = instance[key]
                    # print('global_res_dict[key]: ', instance[key])  # for debugging only
            inst_res_dict = []

        ########### Calculate additional values ##########

        run_instanceCalculations(inst_res_dict)
        run_globalCalculations(global_res_dict,inst_res_dict)

        ############ Get the final result dict ###########

        # Append "global_res_dict" and "inst_res_dict" to "all_dfs" dict
        all_dfs.append(global_res_dict)
        for i in inst_res_dict:
            all_dfs.append(i)

    except Exception as e:
        print("Error while processing this file: " + fileNames[count] + '\n' + '\nMoving on to next...\n')
        print(traceback.format_exc())
        all_dfs.append({'filename': fileNames[count].replace('\\', '/'), 'status': 'FAILED'})
        continue

    # for debugging
    if local_dev and debug:
        print('------ global_res_dict -------')
        print(global_res_dict)
        f = open(os.path.join(outFolder, 'global_res_dict.json'), 'w')
        f.write(str(global_res_dict).replace("'", '"'))

        print('----- inst_res_dict ------')
        print(inst_res_dict)
        f = open(os.path.join(outFolder, 'inst_res_dict.json'), 'w')
        f.write(str(inst_res_dict).replace("'", '"'))

################# Prepare output #################

# Add an unique id to each dict in all_dfs list
# Fill none fields with empty string for excel
id = 0
for file in all_dfs:
    # Add an unique id column
    id += 1
    file['id'] = id
    # Fill none fields with empty string for excel
    for parameter in csvSortedCsvCols:
        if parameter not in file:
            file[parameter] = ''    # mp: should empty values set to 'n.a.|null|not-found' ?

df = pandas.DataFrame(all_dfs)      # read data into pandas framework
dfcsv = df[csvSortedCsvCols]        # fetch data in sorted order using internal used field names

print("----------- all_dfs ----------")
# print(all_dfs)

######## Prepare CSV & Excel for local dev #######

if local_dev:
    if debug:
        print("---------- df.to_csv ---------")
        # print(dfcsv.to_csv(index=False, sep ='='))
        print(dfcsv.to_csv(index=True, sep =';'))
        print("------------- df -------------")
        print(dfcsv)

        # Create all_dfs.json file (for debugging purpose)
        f = open(os.path.join(outFolder, 'all_dfs.json'), 'w')
        f.write(str(all_dfs).replace("'", '"'))

    # Create csv file using defined csv output column names
    # dfcsv.to_csv(os.path.join(outFolder, outFileBase + ".csv"), index=False, sep =';')

    # # Create json file from csv
    # dfcsv.to_json(os.path.join(outFolder, outFileBase + ".json"), orient="records")

    # Create xlsx file using defined xls output column names
    dfxls = df.copy()
    dfxls = dfxls[xlsSortedCsvCols]
    # Rename column names from internal used (csv) field names to xlsx output column names
    # df.set_axis([csv_output_cols], axis='columns', inplace=True)
    # df.set_axis seams to be buggy. First column starts at second column position if using df.to_excel.
    # So we are using df.rename instead of df.set_axis
    dfxls.rename(columns=csv2xsl, inplace=True, errors="raise")
    dfxls.to_excel(os.path.join(outFolder, outFileBase + ".xlsx"), sheet_name="output", index=False, header=True)

# Return for JS (data for csv; header for xls header column name mapping)
# Have to convert csv2xsl and xlsSortedXlsCols into valid json formated strings
# csv2xsl = re.sub("\s*:\s*", ":", str(csv2xsl)).replace("'",'"')
# xlsSortedXlsCols = re.sub("\s*:\s*", ":", str(xlsSortedXlsCols)).replace("'",'"')
# data = str(dfcsv.to_csv(index=False, sep ='='))
# jsReturn = csv2xsl + '|' + xlsSortedXlsCols + '|' + data
# """
# End of Main.py script
# """
# jsReturn
