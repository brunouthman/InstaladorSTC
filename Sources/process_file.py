#########################################################################################
## Brief
## This script process an event register file seeking for a begin mission event type.
## Once found, the prefix and timestamp are extracted from the register and the current
## file being processed is renamed with these data. From this point, additional events
## are recorded until a new begin mission event type are located. This process repeats
## at every execution of log rotate from event register.
##
##
## ART EVENT REGISTER PARSER TOOL
## optional arguments:
## -h, --help     show this help message and exit
## -i INPUT_FILE  Event file to parse with path location
## -pt PT_PATH    Partial trips folder location
## -ct CT_PATH    Complete trips folder location
##
## Usage example:
## process_file.py -i "event.dr" -pt "/data/partial_trips/" -ct "/data/completed_trips"
#########################################################################################
import sys
import argparse
import binascii
from construct import *
import os, random, struct

ARG_HELP_I = 'Event file to parse with path location'
ARG_HELP_PT = 'Partial trips folder location'
ARG_HELP_CT = 'Complete trips folder location'
PT_DEFAULT_FILENAME = 'temp.dr'
DEBUG_MSG_ENABLED = 1
#########################################################################################
## Enumerations
#########################################################################################
class EventTypes(Enum):
    OBC_IDENTIFICATION = 1
    LOGIN = 2
    LOGOUT = 3
    TRAIN_PROFILE = 4
    BEGIN_MISSION_TRAIN = 5
    END_MISSION_TRAIN = 6
    PENALTY_APPLICATION = 7
    PENALTY_RELEASE = 8
    GPS = 9
    TACHO = 10
    NAVIGATION = 11
    SENSORS = 12
    MOVEMENT_AUTHORITY = 13
    SB_TRANSITION = 14
    SB_RELEASE = 15
    COMMUNICATION = 16
    PENALTY_CONTROL = 17
    CHECKLIST = 18
    CONSUMPTION = 19
    GOLDEN_RUN = 20
    DENIED_ACTION = 21
    CONTEXT = 22
    LOCOMOTIVE_STATES = 23
#########################################################################################
## Event structs
#########################################################################################
evt_hdr = Struct("structure_version" / BytesInteger(1),
                 "sequence_number" / Array(4, Byte),
                 "timestamp" / Array(6, Byte),
                 "type" / BytesInteger(1),
                 "data_version" / BytesInteger(1))

evt_tp = Struct("profile_type" / BytesInteger(1),
                           "train_prefix" / Array(16, Byte),
                           "train_os" / Array(16, Byte),
                           "eot_id" / Array(4, Byte),
                           "train_length" / Array(4, Byte),
                           "tb" / Array(4, Byte),
                           "tu" / Array(4, Byte),
                           "train_type" / BytesInteger(1),
                           "structures_qtty" / Array(2, Byte))

evt_tp_vehicle = Struct("vehicle_pos" / BytesInteger(1),
                        "vehicle_type" / BytesInteger(1),
                        "vehicle_id" / Array(8, Byte),
                        "vehicles_qtty" / Array(2, Byte))

evt_comm = Struct("msg_id" / Array(4, Byte),
                  "direction" / BytesInteger(1),
                  "data_size" / Array(2, Byte))

evt_loco_state = Struct("locos_qtty" / BytesInteger(1))

evt_loco_state_variable = Struct("loco_number" / Array(4, Byte),
                                 "locos_state" / BytesInteger(1))

evt_begin_mission = Struct("train_prefix" / Array(16, Byte),
                           "action" / BytesInteger(1),
                           "origin_location" / Array(12, Byte),
                           "destination_location" / Array(12, Byte),
                           "mission_type" / BytesInteger(1))

evt_end_mission = Struct("train_prefix" / Array(16, Byte),
                         "action" / BytesInteger(1),
                         "location" / Array(12, Byte))
#########################################################################################
def get_data_length_by_type(type):
    return{
            EventTypes.OBC_IDENTIFICATION:  37,
            EventTypes.LOGIN:  12,
            EventTypes.LOGOUT:  24,
            EventTypes.TRAIN_PROFILE:  0,
            EventTypes.BEGIN_MISSION_TRAIN:  42,
            EventTypes.END_MISSION_TRAIN:  29,
            EventTypes.PENALTY_APPLICATION:  2,
            EventTypes.PENALTY_RELEASE:  3,
            EventTypes.GPS:  21,
            EventTypes.TACHO: 7,
            EventTypes.NAVIGATION: 30,
            EventTypes.SENSORS: 22,
            EventTypes.MOVEMENT_AUTHORITY: 32,
            EventTypes.SB_TRANSITION: 32,
            EventTypes.SB_RELEASE: 13,
            EventTypes.COMMUNICATION: 0,
            EventTypes.PENALTY_CONTROL: 2,
            EventTypes.CHECKLIST: 4,
            EventTypes.CONSUMPTION: 25,
            EventTypes.GOLDEN_RUN: 7,
            EventTypes.DENIED_ACTION: 2,
            EventTypes.CONTEXT: 44,
            EventTypes.LOCOMOTIVE_STATES: 0,
            }.get(type, -1)    # -1 is default if type was not found
#########################################################################################
def length_of_file(f):
    currentPos=f.tell()
    # Move to end of file
    f.seek(0, 2)
    # Get current position
    length = f.tell()
    # Go back to where we started
    f.seek(currentPos, 0)
    return length
#########################################################################################
def read_from_file(file, bytes_to_read, proc_bytes, byte_array):
    read_bytes = file.read(bytes_to_read)
    proc_bytes += len(read_bytes)
    # Convert string to bytearray type
    byte_array.extend(read_bytes)
    return read_bytes, proc_bytes, byte_array
#########################################################################################
def get_file_from_path(path):
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            return file
#########################################################################################
def print_event_data(int_seq_num, type, single_evt):
    seq = "Sequence: " + str(int_seq_num)
    type = " Type: " + str(type)
    data = " Data: " + ''.join('{:02x}'.format(x) for x in single_evt)

    print_debug( seq + type + data )
#########################################################################################
def timestamp_to_int(timestamp):
    byte_array_timestamp = bytearray(8)
    byte_array_timestamp[:6] = timestamp
    int_timestamp = struct.unpack("<Q", bytearray(byte_array_timestamp))[0]
    return int_timestamp
#########################################################################################
def open_file_again(path, filename):
    pt_file_str = path + filename
    print_debug( "Openning file again:" + pt_file_str )
    pt_file = open(pt_file_str, "ab")
    print_debug( "Sucess" )
    return filename, pt_file
#########################################################################################
def print_debug(debug_message):
    if DEBUG_MSG_ENABLED:
        print( debug_message )
#########################################################################################
def process_event_types(evt_type, file, data_len, proc_bytes, single_evt):

    should_break = False
    # If the returned value is -1, type not recognized (probably padding bytes)
    if data_len == -1:
        should_break = True
    # If the returned value is zero, the event has a variable size
    elif data_len == 0:
        if evt_type == EventTypes.TRAIN_PROFILE:
            # Read only the train profile data size to calculate variable size
            tp_bytes,proc_bytes,single_evt = read_from_file(file, evt_tp.sizeof(), proc_bytes, single_evt)
            # Parse data into train profile struct
            struct_tp = Struct(Embedded(evt_tp))
            parsed_tp = struct_tp.parse(tp_bytes)
            # Train Profile Vehicle size
            tps_size = struct.unpack("<H", bytearray(parsed_tp.structures_qtty))[0]
            # Calculate the offset of variable part
            tpv_size = tps_size * evt_tp_vehicle.sizeof()
            # Read from file the variable part of the event
            vehicle_bytes,proc_bytes,single_evt = read_from_file(file, tpv_size, proc_bytes, single_evt)
            # Parse data into train profile vehicle struct (OPTIONAL)
            # struct_tpv = Struct(Embedded(evt_tp_vehicle))
            # parsed_tpv = struct_tpv.parse(vehicle_bytes)
        elif evt_type == EventTypes.COMMUNICATION:
            # Read only the train profile data size to calculate the variable size
            comm_bytes,proc_bytes,single_evt = read_from_file(file, evt_comm.sizeof(), proc_bytes, single_evt)
            # Parse data into communication struct
            struct_comm = Struct(Embedded(evt_comm))
            parsed_comm = struct_comm.parse(comm_bytes)
            # Get communication variable data size
            comm_data_size = struct.unpack("<H", bytearray(parsed_comm.data_size))[0]
            # Read from file the variable part of the event
            comm_data_bytes,proc_bytes, ingle_evt = read_from_file(file, comm_data_size, proc_bytes, single_evt)
        elif evt_type == EventTypes.LOCOMOTIVE_STATES:
            # Read only the train profile data size to calculate the variable size
            ls_bytes,proc_bytes,single_evt = read_from_file(file, evt_loco_state.sizeof(), proc_bytes, single_evt)
            # Parse data into locomotive states struct
            struct_ls = Struct(Embedded(evt_loco_state))
            parsed_ls = struct_ls.parse(ls_bytes)
            # Locomotives state size
            ls_size = parsed_ls.locos_qtty
            # Calculate the offset of variable part
            ls_size_var = ls_size * evt_loco_state_variable.sizeof()
            # Read from file the variable part of the event
            lsv_bytes,proc_bytes,single_evt = read_from_file(file, ls_size_var, proc_bytes, single_evt)
            # Parse data into locomotive state variable struct (OPTIONAL)
            # struct_lsv = Struct(Embedded(evt_loco_state_variable))
            # parsed_lsv = struct_lsv.parse(lsv_bytes)
        else:
            # Stop processing the file since we dont know how to find the next event
            print_debug( "Unknown variable size event" )
            should_break = True
    else:
        # Read data contents from file
        data_bytes,proc_bytes,single_evt = read_from_file(file, data_len, proc_bytes, single_evt)

        # Define data struct
        msg_data = Struct("data" / Array(data_len, Byte))
        # Parse data
        parsed_data = msg_data.parse(data_bytes)

    return proc_bytes, single_evt, should_break
#########################################################################################
def process_file(file_name, pt_path, ct_path):
    try:
        pt_file_name = ""
        # Check file existence on partial trip folder
        if not os.listdir(pt_path):
            # There is no file inside partial trip folder
            print_debug( "Files not found on partial trip folder" )
            # Creates a temporary file until get trip parameters to rename it
            pt_file_name = PT_DEFAULT_FILENAME
        else:
            # Get the first file inside the folder - normally just one file is allowed
            pt_file_name = get_file_from_path(pt_path)
            # A file already exists inside partial trip folder - append events to it
            print_debug( "File found on partial trip folder: " + pt_file_name )

        # Open the partial trip file on append mode
        with open(pt_path + pt_file_name, "ab") as pt_file:
            # Open the input file, processing every event
            with open(file_name, "rb") as input_file:

                # Get file length
                available_bytes = length_of_file(input_file)
                print_debug( "File size :" + str(available_bytes) )

                while True:
                    proc_bytes = 0
                    single_evt = bytearray()
                    # Initially, parse only header to get the event type
                    header_bytes,proc_bytes,single_evt = read_from_file(input_file, evt_hdr.sizeof(), proc_bytes, single_evt)

                    if header_bytes:
                        # Define header struct
                        msg_aux = Struct(Embedded(evt_hdr))
                        # Parse read bytes into the struct
                        parsed_header = msg_aux.parse(header_bytes)
                        int_seq_num = struct.unpack("<I", bytearray(parsed_header.sequence_number))[0]

                        # Now, calculate the event size based on its type
                        data_len = get_data_length_by_type(parsed_header.type)

                        # If current event is a context, check if the next event is a begin mission event
                        if parsed_header.type == EventTypes.CONTEXT:
                            # Read the rest of the context event
                            data_bytes,proc_bytes,single_evt = read_from_file(input_file, data_len, proc_bytes, single_evt)
                            print_event_data(int_seq_num, parsed_header.type, single_evt)
                            available_bytes -= proc_bytes

                            # By now we have the context event data stored at single_evt variable
                            # Reading the next event to decide where this event must be stored
                            proc_bytes = 0
                            next_evt = bytearray()
                            next_header_bytes,proc_bytes,next_evt = read_from_file(input_file, evt_hdr.sizeof(), proc_bytes, next_evt)
                            # Parse read bytes into the struct
                            next_parsed_header = msg_aux.parse(next_header_bytes)
                            next_int_seq_num = struct.unpack("<I", bytearray(next_parsed_header.sequence_number))[0]
                            next_data_len = get_data_length_by_type(next_parsed_header.type)

                            # Process the remaining of bytes after the header
                            proc_bytes,next_evt, should_break = process_event_types(next_parsed_header.type, input_file, next_data_len, proc_bytes, next_evt)
                            if should_break == True:
                                # Still have a context event recorded, record it and stop processing
                                pt_file.write(single_evt)
                                break

                            if next_parsed_header.type == EventTypes.BEGIN_MISSION_TRAIN:
                                # Parse the begin mission event to extract its data
                                print_debug( "Begin Mission Event" )
                                begin_mission_str = Struct(Embedded(evt_begin_mission))
                                parsed_begin_mission = begin_mission_str.parse(next_evt[evt_hdr.sizeof():])
                                prefix = bytearray()
                                prefix.extend(parsed_begin_mission.train_prefix)
                                print_debug( "BEGIN MISSION TRAIN PREFIX: " + str(prefix).strip('\0') )
                                # Convert timestamp to integer (long long)
                                int_timestamp = timestamp_to_int(parsed_header.timestamp)

                                if pt_file_name == PT_DEFAULT_FILENAME:
                                    # Close the default partial trip file and rename it with the following pattern: timestamp + train_prefix + "_C_" + ".dr"
                                    pt_file.close()

                                    file_renamed = str(int_timestamp) + "_" + str(prefix).strip('\0')  + ".dr"
                                    print_debug( "Partial trip file is default, context - renaming it to: " + file_renamed )

                                    pt_file_str = pt_path + file_renamed
                                    os.rename(pt_path + pt_file_name, pt_file_str)
                                    # Open the renamed file and continue writing on it
                                    pt_file_name, pt_file = open_file_again(pt_path, file_renamed)
                                else:
                                    print_debug( "Partial trip file NOT default" )
                                    # Close the current partial trip file
                                    pt_file.close()
                                    print_debug( "Renaming " + pt_path + pt_file_name + " TO " + ct_path + pt_file_name )
                                    # Move it to the completed_trip folder
                                    os.rename(pt_path + pt_file_name, ct_path + pt_file_name)
                                    # Creates a new partial trip file with begin mission data
                                    begin_mission_file_name = str(int_timestamp) + "_" + str(prefix).strip('\0')  + ".dr"
                                    print_debug( "New partial trip file created: " + begin_mission_file_name )
                                    # Open the renamed file and continue writing on it
                                    pt_file_name, pt_file = open_file_again(pt_path, begin_mission_file_name)

                                # Record the events on the new partial trip file AFTER closing the last file
                                pt_file.write(single_evt)
                                pt_file.write(next_evt)
                            elif next_parsed_header.type == EventTypes.END_MISSION_TRAIN:
                                # Parse the end mission event to extract its data
                                print_debug( "End Mission Event" )
                                end_mission_str = Struct(Embedded(evt_end_mission))
                                parsed_end_mission = end_mission_str.parse(next_evt[evt_hdr.sizeof():])
                                prefix = bytearray()
                                prefix.extend(parsed_end_mission.train_prefix)
                                print_debug( "END MISSION TRAIN PREFIX: " + str(prefix).strip('\0') )

                                # Record the events on the partial trip file BEFORE closing it
                                pt_file.write(single_evt)
                                pt_file.write(next_evt)

                                # Close the current partial trip file
                                pt_file.close()
                                print_debug( "Renaming " + pt_path + pt_file_name + " TO " + ct_path + pt_file_name )
                                # Move it to the completed_trip folder
                                os.rename(pt_path + pt_file_name, ct_path + pt_file_name)
                                # Open file with default name since we dont know the timestamp of next event
                                pt_file_name, pt_file = open_file_again(pt_path, PT_DEFAULT_FILENAME)
                            else:
                                # Generic context type, record it into the current partial_trip file
                                print_event_data(next_int_seq_num, next_parsed_header.type, next_evt)

                                # Record the events on the current partial trip file
                                pt_file.write(single_evt)
                                pt_file.write(next_evt)

                            available_bytes -= proc_bytes
                            # Check available bytes
                            if available_bytes < evt_hdr.sizeof():
                                break
                        else:
                            # Not a context event type - rename the file with the timestamp of first event if default, pattern: timestamp + ".dr"
                            if pt_file_name == PT_DEFAULT_FILENAME:
                                pt_file.close()

                                int_hdr_timestamp = timestamp_to_int(parsed_header.timestamp)
                                file_renamed = str(int_hdr_timestamp) + ".dr"

                                print_debug( "Partial trip file is default, not context - renaming it to: " + file_renamed )
                                os.rename(pt_path + pt_file_name, pt_path + file_renamed)
                                # Once renamed, open the file again to continue recording events on it
                                pt_file_name, pt_file = open_file_again(pt_path, file_renamed)
                            else:
                                print_debug( "Partial trip file NOT default, not context" )
                                # If not default, the file was already renamed, just record the event

                            # Process the remaining bytes after the header
                            proc_bytes,single_evt, should_break = process_event_types(parsed_header.type, input_file, data_len, proc_bytes, single_evt)

                            if should_break == True:
                                break
                            else:
                                # Print current register data
                                print_event_data(int_seq_num, parsed_header.type, single_evt)

                                # Write the event into the partial trip file
                                pt_file.write(single_evt)

                                available_bytes -= proc_bytes

                                # Check available bytes
                                if available_bytes < evt_hdr.sizeof():
                                    break
                    else:
                        break
                # Close the input file
                input_file.close()
        # Close the partial trip file
        pt_file.close()
        # Remove the input file
        os.remove(file_name)
    except IOError as e:
        print_debug( "I/O error({0}): {1}".format(e.errno, e.strerror) )
    except ValueError:
        print_debug( "Could not convert data." )
    except:
        print_debug( "Unexpected error:", sys.exc_info()[0] )
#########################################################################################
def main():
    # Program arguments list definitions
    ap = argparse.ArgumentParser(description='ART EVENT REGISTER PARSER TOOL', add_help=True)
    ap.add_argument('-i', action="store", dest="input_file", help=ARG_HELP_I, type=str, required=True)
    ap.add_argument('-pt', action="store", dest="pt_path", help=ARG_HELP_PT, type=str, required=True)
    ap.add_argument('-ct', action="store", dest="ct_path", help=ARG_HELP_CT, type=str, required=True)

    args = ap.parse_args()
    print_debug( "args.pt_path: " + args.pt_path )
    print_debug( "args.ct_path: " + args.ct_path )

    input_file_path = args.input_file

    # Process file contents
    process_file(input_file_path, args.pt_path, args.ct_path)

#########################################################################################
if __name__ == "__main__":
    main()
