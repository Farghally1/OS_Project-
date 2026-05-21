import struct
from FsConstants import FsConstants
from FatTableManager import FatTableManager

class DirectoryEntry:
    def __init__(self, name, attr, first_cluster, file_size):
        self.name = name
        self.attr = attr
        self.first_cluster = first_cluster
        self.file_size = file_size

class DirectoryManager:
    ENTRY_SIZE = 32

    def __init__(self, vd, fat_manager: FatTableManager):
        self.vd = vd
        self.fat = fat_manager

    # ---------------- Name Helpers ---------------- #

    def FormatNameTo8Dot3(self, name):
        original = name
        # التعديل: شلنا المسافات الزيادة قبل ما نحول الحروف لكبيرة
        name = name.strip().upper()
        parts = name.split(".")

        truncated = False
        fname = parts[0][:8]
        if len(parts[0]) > 8:
            truncated = True

        ext = ""
        if len(parts) > 1:
            ext = parts[1][:3]
            if len(parts[1]) > 3:
                truncated = True

        if truncated:
            print(f"Warning: File name '{original}' is too long. It was saved as '{fname}.{ext}'")

        return (fname.ljust(8) + ext.ljust(3)).encode()

    def Parse8Dot3Name(self, raw):
        raw = raw.decode().rstrip("\x00")
        return raw[:8].strip() + ("." + raw[8:].strip() if raw[8:].strip() else "")

    # ---------------- Directory Read ---------------- #

    def ReadDirectory(self, start_cluster):
        entries = []
        chain = self.fat.FollowChain(start_cluster)

        for cluster in chain:
            data = self.vd.ReadCluster(cluster)
            for i in range(0, FsConstants.CLUSTER_SIZE, self.ENTRY_SIZE):
                chunk = data[i : i + self.ENTRY_SIZE]
                if chunk[0] == 0x00:
                    continue

                name = self.Parse8Dot3Name(chunk[0:11])
                attr = chunk[11]
                first_cluster = struct.unpack("<i", chunk[12:16])[0]
                file_size = struct.unpack("<i", chunk[16:20])[0]

                entries.append(DirectoryEntry(name, attr, first_cluster, file_size))

        return entries

    def FindDirectoryEntry(self, start_cluster, name):
        name = name.strip().upper()
        for entry in self.ReadDirectory(start_cluster):
            if entry.name.upper() == name:
                return entry
        return None

    # ---------------- Add / Update ---------------- #

    def AddDirectoryEntry(self, start_cluster, entry: DirectoryEntry):
        raw = bytearray(self.ENTRY_SIZE)

        name = entry.name
        parts = name.split(".")

        if len(parts[0]) > 8 or (len(parts) > 1 and len(parts[1]) > 3):
            print(f"Warning: File name '{name}' is too long. It will be truncated to 8.3 format.")

        formatted_name_bytes = self.FormatNameTo8Dot3(name)
        raw[0:11] = formatted_name_bytes
        raw[11] = entry.attr
        raw[12:16] = struct.pack("<i", entry.first_cluster)
        raw[16:20] = struct.pack("<i", entry.file_size)

        formatted_name = self.Parse8Dot3Name(formatted_name_bytes)
        chain = self.fat.FollowChain(start_cluster)

        for cluster in chain:
            data = bytearray(self.vd.ReadCluster(cluster))

            for i in range(0, FsConstants.CLUSTER_SIZE, self.ENTRY_SIZE):
                # لو لقينا مكان فاضي
                if data[i] == 0x00:
                    data[i : i + self.ENTRY_SIZE] = raw
                    self.vd.WriteCluster(cluster, data)
                    return

                # لو الملف موجود أصلاً وبنعمله تحديث
                existing = self.Parse8Dot3Name(data[i : i + 11])
                if existing.upper() == formatted_name.upper():
                    data[i : i + self.ENTRY_SIZE] = raw
                    self.vd.WriteCluster(cluster, data)
                    return

        # لو الكلاسترز كلها مليانة، بنحجز كلاستر جديد
        new_cluster = self.fat.AllocateChain(1)
        
        # التعديل: نربط الكلاستر الجديد بآخر كلاستر في الفولدر جوه الـ FAT
        last_cluster_in_chain = chain[-1]
        self.fat.SetFatEntry(last_cluster_in_chain, new_cluster)
        self.fat.FlushFatToDisk()

        # نكتب بيانات الملف الجديد في الكلاستر الفاضي
        empty = bytearray(FsConstants.CLUSTER_SIZE)
        empty[0 : self.ENTRY_SIZE] = raw
        self.vd.WriteCluster(new_cluster, empty)

    # ---------------- Remove ---------------- #

    def RemoveDirectoryEntry(self, start_cluster, name):
        chain = self.fat.FollowChain(start_cluster)

        for cluster in chain:
            data = bytearray(self.vd.ReadCluster(cluster))
            for i in range(0, FsConstants.CLUSTER_SIZE, self.ENTRY_SIZE):
                if data[i] == 0x00:
                    continue

                existing = self.Parse8Dot3Name(data[i : i + 11])
                if existing.upper() == name.strip().upper():
                    # التعديل: نقرأ رقم أول كلاستر للملف عشان نفضيه
                    first_cluster = struct.unpack("<i", data[i+12 : i+16])[0]
                    
                    # نمسح الملف من الفولدر (نكتب أصفار)
                    data[i : i + self.ENTRY_SIZE] = bytes(self.ENTRY_SIZE)
                    self.vd.WriteCluster(cluster, data)
                    
                    # التعديل: نفضي المساحة من الـ FAT
                    if first_cluster != 0:
                        self.fat.FreeChain(first_cluster)
                        
                    return True

        return False