# NSKeyedArchive plist deserializer
Deserializes NSKeyedArchiver created plists, which are frequent in macOS/iOS. These are serialized versions of plists (or data classes) and are meant for machine reading. The deserialized version is human readable for analysts and investigators who need to review the data.

The library recursively deserializes the entire plist and returns a dictionary/list object representing the entire plist. Certain NSKeyedArchiver plists contain circular references, which results in infinite looping. The code detects and breaks these loops wherever found to return useable data.

#### Requirements: Python 3.6+ (3.8 recommended)
Due to improvements in the built-in `plistlib` library in Python 3.8, it is recommended to use 3.8 or above. For 3.7 or lower, it should work fine for most plists, some might fail to save correctly. If you don't care about saving the deserialized plist (using the built-in library functions), then this should make no difference.

#### Installation (via pip/pip3)
```
pip3 install nska_deserialize
```

#### Usage

```
import nska_deserialize as nd

input_path = '/Users/yogesh/Desktop/sample.sfl2'

with open(input_path, 'rb') as f:
    try:
        deserialized_plist = nd.deserialize_plist(f)
        print(deserialized_plist)
    except (nd.DeserializeError, biplist.NotBinaryPlistException, 
            ccl_bplist.BplistError, ValueError, 
            TypeError, OSError, OverflowError) as ex:
        # These are all possible errors from libraries imported
        print('Had exception: ' + str(ex))
        deserialized_plist = None

    if deserialized_plist:
        output_path_plist = input_path + '_deserialized.plist'
        output_path_json  = input_path + '_deserialized.json'

        nd.write_plist_to_json_file(deserialized_plist, output_path_json)
        nd.write_plist_to_file(deserialized_plist, output_path_plist)
```