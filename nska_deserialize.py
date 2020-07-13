"""
Converts NSKeyedArchiver plists to their deserialized versions.

(c) 2020 Yogesh Khatri <yogesh@swiftforensics.com>, MIT License

Usage
-----

import nska_deserialize as nd

input_path = 'C:\\temp\\demo.plist'

with open(input_path, 'rb') as f:
    try:
        deserialized_plist = nd.deserialize_plist(f) # Get Deserialized plist
    except (nd.DeserializeError, biplist.NotBinaryPlistException, ccl_bplist.BplistError,
             ValueError, TypeError, OSError, OverflowError) as ex:
        # These are all possible errors from libraries imported
        print('Had exception: ' + str(ex))
        deserialized_plist = None

    if deserialized_plist:
        output_path_plist = input_path + '_deserialized.plist'
        output_path_json  = input_path + '_deserialized.json'

        nd.write_plist_to_json_file(deserialized_plist, output_path_json)
        nd.write_plist_to_file(deserialized_plist, output_path_plist)


"""

import biplist
import ccl_bplist
import io
import json
import plistlib

deserializer_version = '1.2'

rec_depth = 0
rec_uids = []

class DeserializeError(Exception):
    pass

def get_version():
    global deserializer_version
    return deserializer_version

def _recurse_safely(uid, plist, root, object_table):
    '''Returns False if infinite recursion was detected'''
    global rec_uids
    if uid in rec_uids:
        #print(f'INFINITE RECURSION detected - breaking loop! uid={uid} , LIST={str(rec_uids)}')
        return False
    rec_uids.append(uid)
    _recurse_create_plist(plist, root, object_table)
    rec_uids.pop()
    return True

def _recurse_create_plist(plist, root, object_table):
    global rec_depth
    rec_depth += 1
    
    #if rec_depth > 50:
    #    print('Possible infinite recursion detected!!')
    if isinstance(root, dict):
        for key, value in root.items():
            if key == '$class': 
                continue
            add_this_item = True
            v = None
            if isinstance(value, ccl_bplist.BplistUID):
                v2 = ccl_bplist.NSKeyedArchiver_convert(object_table[value.value], object_table)
                if isinstance(v2, dict):
                    v = {}
                    add_this_item = _recurse_safely(value.value, v, v2, object_table)
                elif isinstance(v2, list):
                    v = []
                    add_this_item = _recurse_safely(value.value, v, v2, object_table)
                else:
                    v = v2
            elif isinstance(value, list):
                v = []
                _recurse_create_plist(v, value, object_table)
            elif isinstance(value, dict):
                v = {}
                _recurse_create_plist(v, value, object_table)
            else:
                v = value
            # change None to empty string. This is because if an object value is $null, it
            # is most likely going to be a string. This has to be done, else writing a plist back will fail.
            if v == None:
                v = ''
            # Keys must be string, else plist writing will fail!
            if not isinstance(key, str):
                key = str(key)
            if add_this_item:
                plist[key] = v
    else: # must be list
        for value in root:
            v = None
            add_this_item = True
            if isinstance(value, ccl_bplist.BplistUID):
                v2 = ccl_bplist.NSKeyedArchiver_convert(object_table[value.value], object_table)
                if isinstance(v2, dict):
                    v = {}
                    add_this_item = _recurse_safely(value.value, v, v2, object_table)
                elif isinstance(v2, list):
                    v = []
                    add_this_item = _recurse_safely(value.value, v, v2, object_table)
                else:
                    v = v2
            elif isinstance(value, list):
                v = []
                _recurse_create_plist(v, value, object_table)
            elif isinstance(value, dict):
                v = {}
                _recurse_create_plist(v, value, object_table)
            else:
                v = value
            # change None to empty string. This is because if an object value is $null, it
            # is most likely going to be a string. This has to be done, else writing a plist back will fail.
            if v == None:
                v = ''
            if add_this_item:
                plist.append(v)
    rec_depth -= 1
    
def _convert_CFUID_to_UID(plist):
    ''' For converting XML plists to binary, UIDs which are represented
        as strings 'CF$UID' must be translated to actual UIDs.
    '''
    if isinstance(plist, dict):
        for k, v in plist.items():
            if isinstance(v, dict):
                num = v.get('CF$UID', None)
                if (num is None) or (not isinstance(num, int)):
                    _convert_CFUID_to_UID(v)
                else:
                    plist[k] = biplist.Uid(num)
            elif isinstance(v, list):
                _convert_CFUID_to_UID(v)
    else: # list
        for index, v in enumerate(plist):
            if isinstance(v, dict):
                num = v.get('CF$UID', None)
                if (num is None) or (not isinstance(num, int)):
                    _convert_CFUID_to_UID(v)
                else:
                    plist[index] = biplist.Uid(num)
            elif isinstance(v, list):
                _convert_CFUID_to_UID(v)

def _get_root_element_names(f):
    ''' The top element is usually called "root", but sometimes it is not!
        Hence we retrieve the correct name here. In some plists, there is
        more than one top element, this function will retrieve them all.
    '''
    roots = []

    plist = biplist.readPlist(f)
    top_element = plist.get('$top', None)
    if top_element:
        roots = [ x for x in top_element.keys() ]
    else:
        raise NskaDeserializeError('$top element not found! Not an NSKeyedArchive?')

    return roots

def _get_valid_nska_plist(f):
    '''Checks if there is an embedded NSKeyedArchiver plist as a data blob. On 
       ios, several files are like that. Also converts any xml based plist to 
       binary plist. Returns a file object representing a binary plist file.
    '''
    plist = biplist.readPlist(f)
    if isinstance(plist, bytes):
        data = plist
        f = io.BytesIO(data)
    f.seek(0)

    # Check if file to be returned is an XML plist
    header = f.read(8)
    f.seek(0)
    if header[0:6] != b'bplist': # must be xml
        # Convert xml to binary (else ccl_bplist wont load!)
        tempfile = io.BytesIO()
        plist = biplist.readPlist(f)
        _convert_CFUID_to_UID(plist)
        biplist.writePlist(plist, tempfile)
        tempfile.seek(0)
        return tempfile

    return f

def deserialize_plist(path_or_file):
    '''
        Returns a deserialized plist as a dictionary/list. 

        Parameters
        ----------
        path_or_file:
            Path or file-like object of an NSKeyedArchive file
        
        Returns
        -------
        A dictionary or list is returned depending on contents of 
        the plist

        Exceptions
        ----------
        nska_deserialize.DeserializeError, 
        biplist.NotBinaryPlistException, 
        ccl_bplist.BplistError,
        ValueError, 
        TypeError, 
        OSError, 
        OverflowError
    '''
    path = ''
    f = None
    if isinstance(path_or_file, str):
        path = path_or_file
        f = open(path, 'rb')
    else: # its a file
        f = path_or_file

    f = _get_valid_nska_plist(f)
    ccl_bplist.set_object_converter(ccl_bplist.NSKeyedArchiver_common_objects_convertor)
    plist = ccl_bplist.load(f)
    ns_keyed_archiver_obj = ccl_bplist.deserialise_NsKeyedArchiver(plist, parse_whole_structure=True)

    root_names = _get_root_element_names(f)
    top_level = []

    for root_name in root_names:
        root = ns_keyed_archiver_obj[root_name]
        if isinstance(root, dict):
            plist = {}
            _recurse_create_plist(plist, root, ns_keyed_archiver_obj.object_table)
            if root_name.lower() != 'root':
                plist = { root_name : plist }
        elif isinstance(root, list):
            plist = []
            _recurse_create_plist(plist, root, ns_keyed_archiver_obj.object_table)
            if root_name.lower() != 'root':
                plist = { root_name : plist }
        else:
            plist = { root_name : root }
        
        if len(root_names) == 1:
            top_level = plist
        else: # > 1
            top_level.append(plist)

    return top_level

def _get_json_writeable_plist(in_plist, out_plist):
    if isinstance(in_plist, list):
        for item in in_plist:
            if isinstance(item, list):
                i = []
                out_plist.append(i)
                _get_json_writeable_plist(item, i)
            elif isinstance(item, dict):
                i = {}
                out_plist.append(i)
                _get_json_writeable_plist(item, i)
            elif isinstance(item, bytes):
                out_plist.append(item.hex())
            else:
                out_plist.append(str(item))
    else: #dict
        for k, v in in_plist.items():
            if isinstance(v, list):
                i = []
                out_plist[k] = i
                _get_json_writeable_plist(v, i)
            elif isinstance(v, dict):
                i = {}
                out_plist[k] = i
                _get_json_writeable_plist(v, i)
            elif isinstance(v, bytes):
                out_plist[k] = v.hex()
            else:
                out_plist[k] = str(v)

def write_plist_to_json_file(deserialized_plist, output_path):
    '''
        Converts the plist to a json file and writes it out.

        Parameters
        ----------
        deserialized_plist:
            A dictionary/list representing a plist

        output_path
            Path (including filename) where file will be saved

        Exceptions
        ----------
        Json may raise TypeError, ValueError
    '''

    out_file = open(output_path, 'w')

    json_plist = {} if isinstance(deserialized_plist, dict) else []
    _get_json_writeable_plist(deserialized_plist, json_plist)
    json.dump(json_plist, out_file)
    out_file.close()

def write_plist_to_file(deserialized_plist, output_path):
    '''
        Write a plist back out to a file as a binary plist. Use this function only with
        Python >= 3.8, as write support is broken for earlier versions.

        Parameters
        ----------
        deserialized_plist:
            A dictionary/list representing a plist

        output_path
            Path (including filename) where file will be saved

        Exceptions
        ----------
        OverflowError, ValueError
    '''
    out_file = open(output_path, 'wb')
    plistlib.dump(deserialized_plist, out_file, fmt=plistlib.FMT_BINARY)
    out_file.close()
