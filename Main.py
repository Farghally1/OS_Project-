from VirtualDisk import VirtualDisk
from FsConstants import FsConstants
from FatTableManager import FatTableManager
from DirectoryManager import DirectoryManager
from FileSystem import FileSystem 

def main():
    print("=== اختبار شامل لنظام الملفات ===")

    # 1. تهيئة النظام
    disk = VirtualDisk()
    disk.Initialize("my_os_disk.bin", createIfMissing=True)
    fat = FatTableManager(disk)
    fat.LoadFatFromDisk()
    
    # فورمات للفولدر الرئيسي لو الديسك جديد
    if fat.GetFatEntry(FsConstants.ROOT_DIR_FIRST_CLUSTER) == 0:
        fat.SetFatEntry(FsConstants.ROOT_DIR_FIRST_CLUSTER, -1)
        fat.FlushFatToDisk()

    dir_manager = DirectoryManager(disk, fat)
    fs = FileSystem(disk, fat, dir_manager)
    root = FsConstants.ROOT_DIR_FIRST_CLUSTER
    print("[+] النظام جاهز للعمل.\n")

    try:
        print("------------------------------------------------")
        
        # 1. إنشاء ملف وكتابة وقراءة
        print("1. جاري إنشاء ملف 'TEST.TXT'...")
        fs.create_file(root, "TEST.TXT")
        
        print("2. جاري الكتابة جوه الملف...")
        fs.write_file(root, "TEST.TXT", "بسم الله.. دي تجربة كتابة داتا جوه الملف.")
        
        print("3. جاري قراءة الملف...")
        print(f"   النتيجة: {fs.read_file(root, 'TEST.TXT')}")
        
        # 2. إعادة التسمية (Rename)
        print("\n4. جاري تغيير اسم الملف من 'TEST.TXT' لـ 'NEW.TXT'...")
        fs.rename_entry(root, "TEST.TXT", "NEW.TXT")
        
        # 3. النسخ (Copy)
        print("5. جاري نسخ 'NEW.TXT' لملف جديد اسمه 'COPY.TXT'...")
        fs.copy_file(root, "NEW.TXT", root, "COPY.TXT")
        
        # 4. النقل (Move)
        print("6. جاري نقل 'COPY.TXT' لاسم 'MOVED.TXT' (ده هيمسح COPY.TXT)...")
        fs.move_file(root, "COPY.TXT", root, "MOVED.TXT")
        
        # 5. التعامل مع الفولدرات
        print("\n7. جاري إنشاء فولدر جديد اسمه 'MYDIR'...")
        fs.create_directory(root, "MYDIR")
        
        # 6. المسح (Delete)
        print("8. جاري مسح الملف الأصلي 'NEW.TXT'...")
        fs.delete_file(root, "NEW.TXT")
        
        print("9. جاري مسح الفولدر 'MYDIR'...")
        fs.remove_directory(root, "MYDIR")

        print("------------------------------------------------")
        print("\n[+] التجربة خلصت! نعرض بقى اللي اتبقى في الفولدر الرئيسي:")
        entries = dir_manager.ReadDirectory(root)
        if not entries:
            print("   الفولدر فاضي تماماً!")
        else:
            for entry in entries:
                file_type = "<DIR>" if entry.attr == 1 else "<FILE>"
                print(f"   - {entry.name.strip()} \t {file_type} \t Size: {entry.file_size} Bytes")

    except Exception as e:
        print(f"\n[!] حصلت مشكلة وإحنا بنجرب: {e}")

    finally:
        # قفل النظام بأمان
        fat.FlushFatToDisk()
        disk.CloseDisk()
        print("\n[+] تم قفل الديسك وحفظ البيانات بأمان.")

if __name__ == "__main__":
    main()