from FsConstants import FsConstants


class SuperblockManager:

    def __init__(self, VirtualDisk):
        self.vd = VirtualDisk

    def ReadSuperblock(self):
        return self.vd.ReadCluster(FsConstants.SUPERBLOCK_CLUSTER)

    def WriteSuperblock(self, data: bytes):

        if not isinstance(data, (bytes, bytearray)):
            raise ValueError("Superblock data must be bytes or bytearray")

        if len(data) != FsConstants.CLUSTER_SIZE:
            raise ValueError(f"Superblock must be exactly {FsConstants.CLUSTER_SIZE} bytes long")

        self.vd.WriteCluster(FsConstants.SUPERBLOCK_CLUSTER, data)
