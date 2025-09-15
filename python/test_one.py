import unittest
from textwrap import dedent as dd
from one import OneParser

LEGACY_AUGEAS_GET_TESTS = [
    dd('''
        ENTRY = 123
    '''),
    dd('''
        ENTRY = "MANAGE ABC"
    '''),
    dd('''
        TM_MAD_CONF = [NAME=123]
    '''),
    dd('''
        A = [ NAME=123 ]
    '''),
    dd('''
        A = [
        NAME=123
        ]
    '''),
    dd('''
        A = [
        NAME=123,  NAME2=2
        ]
    '''),
    dd('''
        LOG = [
          SYSTEM      = "file",
          DEBUG_LEVEL = 3
        ]
    '''),
    dd('''
        A=1
        # comment
          # comment with leading space
        \t# comment with leading tab
    '''),
    dd('''
        A=1
        A=1
        B=2 # comment
        # abc
        #

          C=[
          A="B",
          A="B",#abc
          # abc
          X="Y",
          A=123
        ]
    '''),
    dd('''
        C=[
          A=123,  #abc
          B=223# abc
        ]
    '''),
    dd('''
        TM_MAD = [
            EXECUTABLE = "one_tm",
            ARGUMENTS = "-t 15 -d dummy,lvm,shared,fs_lvm,qcow2,ssh,ceph,dev,vcenter,iscsi_libvirt"
        ]
        INHERIT_DATASTORE_ATTR  = "CEPH_HOST"
    '''),
    dd('''
        LOG = [
          SYSTEM      = "file",
          DEBUG_LEVEL = 3
        ]

        MONITORING_INTERVAL_HOST      = 180
        MONITORING_INTERVAL_VM        = 180
        MONITORING_INTERVAL_DATASTORE = 300
        MONITORING_INTERVAL_MARKET    = 600
        MONITORING_THREADS  = 50

        SCRIPTS_REMOTE_DIR=/var/tmp/one
        PORT = 2633
        LISTEN_ADDRESS = "0.0.0.0"
        DB = [ BACKEND = "sqlite" ]

        VNC_PORTS = [
            START    = 5900
        ]

        FEDERATION = [
            MODE          = "STANDALONE",
            ZONE_ID       = 0,
            SERVER_ID     = -1,
            MASTER_ONED   = ""
        ]

        RAFT = [
            LIMIT_PURGE          = 100000,
            LOG_RETENTION        = 500000,
            LOG_PURGE_TIMEOUT    = 600,
            ELECTION_TIMEOUT_MS  = 2500,
            BROADCAST_TIMEOUT_MS = 500,
            XMLRPC_TIMEOUT_MS    = 450
        ]

        DEFAULT_COST = [
            CPU_COST    = 0,
            MEMORY_COST = 0,
            DISK_COST   = 0
        ]

        NETWORK_SIZE = 254

        MAC_PREFIX   = "02:00"

        VLAN_IDS = [
            START    = "2",
            RESERVED = "0, 1, 4095"
        ]

        VXLAN_IDS = [
            START = "2"
        ]

        DATASTORE_CAPACITY_CHECK = "yes"

        DEFAULT_DEVICE_PREFIX       = "hd"
        DEFAULT_CDROM_DEVICE_PREFIX = "hd"

        DEFAULT_IMAGE_TYPE           = "OS"
        IM_MAD = [
              NAME       = "collectd",
              EXECUTABLE = "collectd",
              ARGUMENTS  = "-p 4124 -f 5 -t 50 -i 60" ]

        IM_MAD = [
              NAME          = "kvm",
              SUNSTONE_NAME = "KVM",
              EXECUTABLE    = "one_im_ssh",
              ARGUMENTS     = "-r 3 -t 15 -w 90 kvm" ]

        IM_MAD = [
              NAME          = "vcenter",
              SUNSTONE_NAME = "VMWare vCenter",
              EXECUTABLE    = "one_im_sh",
              ARGUMENTS     = "-c -t 15 -r 0 vcenter" ]

        IM_MAD = [
              NAME          = "ec2",
              SUNSTONE_NAME = "Amazon EC2",
              EXECUTABLE    = "one_im_sh",
              ARGUMENTS     = "-c -t 1 -r 0 -w 600 ec2" ]

        VM_MAD = [
            NAME           = "kvm",
            SUNSTONE_NAME  = "KVM",
            EXECUTABLE     = "one_vmm_exec",
            ARGUMENTS      = "-t 15 -r 0 kvm",
            DEFAULT        = "vmm_exec/vmm_exec_kvm.conf",
            TYPE           = "kvm",
            KEEP_SNAPSHOTS = "no",
            LIVE_RESIZE    = "no",
            IMPORTED_VMS_ACTIONS = "terminate, terminate-hard, hold, release, suspend,
                resume, delete, reboot, reboot-hard, resched, unresched, disk-attach,
                disk-detach, nic-attach, nic-detach, snapshot-create, snapshot-delete"
        ]
    '''),
    dd('''
        PASSWORD = "open\\"nebula"
    '''),
    dd('''
        DB = [
          PASSWORD = "open\\"nebula"
        ]
    '''),
    ' NIC      = [ model="virtio" ]   '
]

MATCH_AND_GET_TESTS = [{
    "input": dd('''
        A = 1
        S = 2
        D = 3
    '''),
    "path": 'S',
    "match": ['S'],
    "value": None,
    "get": ['2']
},{
    "input": dd('''
        A = 1
        S = 2
        S = 2
        D = 3
    '''),
    "path": 'S',
    "match": ['S[1]', 'S[2]'],
    "value": None,
    "get": ['2', '2']
},{
    "input": dd('''
        A = 1
        S = [D = 2]
        S = [D = 3]
    '''),
    "path": 'S',
    "match": [],
    "value": None,
    "get": []
},{
    "input": dd('''
        A = 1
        S = [D = 2]
        S = [D = 3]
    '''),
    "path": 'S/D',
    "match": ['S[1]/D', 'S[2]/D'],
    "value": None,
    "get": ['2', '3']
},{
    "input": dd('''
        A = 1
        S = [D = 2]
        S = [D = 3, D = 4]
    '''),
    "path": 'S[2]/D',
    "match": ['S[2]/D[1]', 'S[2]/D[2]'],
    "value": None,
    "get": ['3', '4']
},{
    "input": dd('''
        A = 1
        S = [D = 2]
        S = [D = 3, D = 4]
    '''),
    "path": 'S[2]/D[2]',
    "match": ['S[2]/D[2]'],
    "value": None,
    "get": ['4']
},{
    "input": dd('''
        A = 1
        S = [D = 2]
        S = [D = 3, D = 4]
    '''),
    "path": '*/D[2]',
    "match": ['S[2]/D[2]'],
    "value": None,
    "get": ['4']
},{
    "input": dd('''
        A = 1
        S = [D = 2]
        S = [D = 3, D = 4]
    '''),
    "path": '*',
    "match": ['A'],
    "value": None,
    "get": ['1']
},{
    "input": dd('''
        A = 1
        S = [D = 2]
        S = [D = 3, D = 4]
    '''),
    "path": '*/*',
    "match": ['S[1]/D', 'S[2]/D[1]', 'S[2]/D[2]'],
    "value": None,
    "get": ['2', '3', '4']
},{
    "input": dd('''
        A = 1
        S = [D = 2]
        S = [D = 3, D = 4]
    '''),
    "path": '*[2]/*',
    "match": ['S[2]/D[1]', 'S[2]/D[2]'],
    "value": None,
    "get": ['3', '4']
},{
    "input": dd('''
        A = 1
        S = [D = 2]
        S = [D = 3, D = 4]
    '''),
    "path": '*/*[2]',
    "match": ['S[2]/D[2]'],
    "value": None,
    "get": ['4']
},{
    "input": dd('''
        A = 1
        S = [D = 2]
        S = [D = 3, D = 4]
    '''),
    "path": '*[2]/*[1]',
    "match": ['S[2]/D[1]'],
    "value": None,
    "get": ['3']
},{
    "input": dd('''
        A = 1
        S = 2
        S = 3
    '''),
    "path": '*',
    "match": ['A', 'S[1]', 'S[2]'],
    "value": None,
    "get": ['1', '2', '3']
},{
    "input": dd('''
        A = 1
        S = 2
        S = 3
    '''),
    "path": 'A[0]',
    "match": [],
    "value": None,
    "get": []
},{
    "input": dd('''
        A = 1
        S = 2
        S = 3
        D = 4
        D = 5
    '''),
    "path": 'S[0]',
    "match": ['S[1]', 'S[2]'],
    "value": None,
    "get": ['2', '3']
},{
    "input": dd('''
        A = 1
        S = 2
        S = 3
        D = 4
        D = 5
    '''),
    "path": '*[0]',
    "match": ['S[1]', 'S[2]', 'D[1]', 'D[2]'],
    "value": None,
    "get": ['2', '3', '4', '5']
},{
    "input": dd('''
        A = 1
        S = 2
        S = 3
        D = 4
        D = 5
    '''),
    "path": '*[0]',
    "match": ['S[2]'],
    "value": '3',
    "get": ['2', '3', '4', '5']
}]

PUT_TESTS = [{
    "input": dd('''
    '''),
    "path": 'A',
    "value": '1',
    "put": dd('''
        A = 1
    ''')
},{
    "input": dd('''
        A = 1
    '''),
    "path": 'S',
    "value": '2',
    "put": dd('''
        A = 1
        S = 2
    ''')
},{
    "input": dd('''
        A = 1
        S = 2
    '''),
    "path": 'S',
    "value": '3',
    "put": dd('''
        A = 1
        S = 3
    ''')
},{
    "input": dd('''
        A = 1
    '''),
    "path": 'A[0]',
    "value": '2',
    "put": dd('''
        A = 1
        A = 2
    ''')
},{
    "input": dd('''
        A = 1
        S = 2
    '''),
    "path": 'S[0]',
    "value": '3',
    "put": dd('''
        A = 1
        S = 2
        S = 3
    ''')
},{
    "input": dd('''
        A = 1
        S = 2 # ASD
        # DSA
    '''),
    "path": 'S[0]',
    "value": '3',
    "put": dd('''
        A = 1
        S = 2 # ASD
        # DSA
        S = 3
    ''')
},{
    "input": dd('''
        A = 1
        S = [D = 2]
    '''),
    "path": 'S/D',
    "value": '3',
    "put": dd('''
        A = 1
        S = [D = 3]
    ''')
},{
    "input": dd('''
        A = 1
        S = [D = 2]
    '''),
    "path": 'S/D[0]',
    "value": '3',
    "put": dd('''
        A = 1
        S = [D = 2,D = 3]
    ''')
},{
    "input": dd('''
        A = 1
        S = [ D = 2 ]
    '''),
    "path": 'S/D[0]',
    "value": '3',
    "put": dd('''
        A = 1
        S = [ D = 2, D = 3 ]
    ''')
},{
    "input": dd('''
        A = 1
        S = [
          D = 2 ]
    '''),
    "path": 'S/D[0]',
    "value": '3',
    "put": dd('''
        A = 1
        S = [
          D = 2,
          D = 3 ]
    ''')
},{
    "input": dd('''
        A = 1
        S = [
          D = 2 # ASD
        ] # DSA
    '''),
    "path": 'S/D[0]',
    "value": '3',
    "put": dd('''
        A = 1
        S = [
          D = 2, # ASD
          D = 3 ] # DSA
    ''')
},{
    "input": dd('''
        A = 1
        S = [

          D = 2 # ASD

        ]
    '''),
    "path": 'S/D[0]',
    "value": '3',
    "put": dd('''
        A = 1
        S = [

          D = 2, # ASD

          D = 3 ]
    ''')
}]

DROP_TESTS = [{
    "input": dd('''
        A = 1
        S = 2
        D = 3
    '''),
    "path": 'S',
    "value": None,
    "drop": dd('''
        A = 1
        D = 3
    ''')
},{
    "input": dd('''
        A = 1
        S = [D = 2,D = 3]
    '''),
    "path": 'S/D[1]',
    "value": None,
    "drop": dd('''
        A = 1
        S = [D = 3]
    ''')
},{
    "input": dd('''
        A = 1
        S = [D = 2,D = 3]
    '''),
    "path": 'S/D[2]',
    "value": None,
    "drop": dd('''
        A = 1
        S = [D = 2]
    ''')
},{
    "input": dd('''
        A = 1
        S = [D = 2]
    '''),
    "path": 'S',
    "value": None,
    "drop": dd('''
        A = 1
        S = [D = 2]
    ''')
},{
    "input": dd('''
        A = 1
        S = [D = 2]
    '''),
    "path": 'S/D',
    "value": None,
    "drop": dd('''
        A = 1
    ''')
},{
    "input": dd('''
        A = 1
        S = [
          D = 2, # ASD
          D = 3 ]
    '''),
    "path": 'S/D[1]',
    "value": None,
    "drop": dd('''
        A = 1
        S = [
          D = 3 ]
    ''')
},{
    "input": dd('''
        A = 1
        S = [
          D = 2, # ASD
          D = 3 ]
    '''),
    "path": 'S/D[2]',
    "value": None,
    "drop": dd('''
        A = 1
        S = [
          D = 2 # ASD
        ]
    ''')
}]

class TestOne(unittest.TestCase):
    def test_AugeasLegacyGet(self):
        for aug in LEGACY_AUGEAS_GET_TESTS:
            op = OneParser(aug)
            op.parse()
            self.assertEqual(op.render(), aug)

    def test_MatchAndGet(self):
        for d in MATCH_AND_GET_TESTS:
            op = OneParser(d['input'])
            op.parse()
            self.assertEqual(op.match(d['path'], d['value']), d['match'])
            self.assertEqual(op.get(d['path']), d['get'])

    def test_Put(self):
        for d in PUT_TESTS:
            op = OneParser(d['input'])
            op.parse()
            op.put(d['path'], d['value'])
            self.assertEqual(op.render(), d['put'])

    def test_Drop(self):
        for d in DROP_TESTS:
            op = OneParser(d['input'])
            op.parse()
            op.drop(d['path'], d['value'])
            self.assertEqual(op.render(), d['drop'])

if __name__ == '__main__':
    unittest.main()
