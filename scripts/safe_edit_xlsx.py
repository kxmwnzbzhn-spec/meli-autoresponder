"""safe_edit_xlsx.py — wrapper para editar cualquier xlsx con backup automatico.

Uso desde otros scripts:
  from safe_edit_xlsx import open_safe, save_safe
  wb = open_safe("/path/to/file.xlsx")  # crea backup automatico
  # ... editar wb
  save_safe(wb, "/path/to/file.xlsx", reason="actualizar emails")

O CLI:
  python safe_edit_xlsx.py backup /path/to/file.xlsx
  python safe_edit_xlsx.py list-backups /path/to/file.xlsx
  python safe_edit_xlsx.py restore /path/to/backup.xlsx /path/to/file.xlsx
"""
import os,shutil,sys,glob
from datetime import datetime
from openpyxl import load_workbook

def backup_path(file_path, reason=None):
    d=os.path.dirname(file_path)
    name=os.path.basename(file_path).rsplit(".",1)[0]
    ts=datetime.now().strftime("%Y%m%d_%H%M%S")
    bdir=os.path.join(d,"backups")
    os.makedirs(bdir,exist_ok=True)
    suffix=f"_{reason}" if reason else ""
    return os.path.join(bdir,f"{name}_{ts}{suffix}.xlsx")

def make_backup(file_path, reason=None):
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)
    b=backup_path(file_path,reason)
    shutil.copy2(file_path,b)
    print(f"  ✓ backup → {b}")
    return b

def open_safe(file_path, reason="auto"):
    make_backup(file_path,reason)
    return load_workbook(file_path)

def save_safe(wb, file_path, reason="edit"):
    # backup ya se hizo en open_safe; este guarda
    wb.save(file_path)
    # Append a un log
    log_path=os.path.join(os.path.dirname(file_path),".edit_log.txt")
    with open(log_path,"a") as f:
        f.write(f"{datetime.now().isoformat()}\t{os.path.basename(file_path)}\t{reason}\n")
    print(f"  ✓ saved → {file_path} (log: {log_path})")

def list_backups(file_path):
    d=os.path.dirname(file_path)
    name=os.path.basename(file_path).rsplit(".",1)[0]
    bdir=os.path.join(d,"backups")
    backups=sorted(glob.glob(f"{bdir}/{name}_*.xlsx"))
    for b in backups[-10:]:
        sz=os.path.getsize(b)
        mt=datetime.fromtimestamp(os.path.getmtime(b)).isoformat()
        print(f"  {mt} {sz:>10} {b}")
    return backups

def restore(backup_file, target_file):
    if not os.path.exists(backup_file):
        raise FileNotFoundError(backup_file)
    # Backup actual antes de restaurar
    if os.path.exists(target_file):
        make_backup(target_file,"pre_restore")
    shutil.copy2(backup_file,target_file)
    print(f"  ✓ restored {backup_file} → {target_file}")

if __name__=="__main__":
    cmd=sys.argv[1] if len(sys.argv)>1 else "help"
    if cmd=="backup":
        make_backup(sys.argv[2], sys.argv[3] if len(sys.argv)>3 else "manual")
    elif cmd=="list-backups":
        list_backups(sys.argv[2])
    elif cmd=="restore":
        restore(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
