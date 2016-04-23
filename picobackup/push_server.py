import os
from SimpleXMLRPCServer import SimpleXMLRPCRequestHandler
from SimpleXMLRPCServer import SimpleXMLRPCServer

import pyrsync as rsync

from picobackup.exceptions import FileExistsError
from picobackup.filesystem import create_dirs


class PushServer:
    """ Simple push server to backup files to a directory """

    # --- PUBLIC INTERFACE --- #

    def __init__(self, address, base_dir):
        self.address = address
        self.base_dir = base_dir

        # initialize the rpc server
        self.rpc_server = SimpleXMLRPCServer(
            address, allow_none=True,
            requestHandler=SimpleXMLRPCRequestHandler)

        self.rpc_server.register_instance(PushServerInterface(self))

    def push(self, file_path, data):
        """
        Pushes a new file to the server. The file_path is the path to store
        the new file and it is relative to the base directory of the server.

        :param file_path: path where to store the file (relative to base
        directory)
        :param data: pushed data to be stored (already decoded).
        """
        file_complete_path = os.path.join(self.base_dir, file_path)

        if os.path.exists(file_complete_path):
            raise FileExistsError(file_complete_path)

        create_dirs(file_complete_path)

        # save the new file
        self.__save(file_complete_path, data)

    def push_dir(self, dir_path):
        """
        Pushes a new directory to the server. The dir_path is the path to the
        new directory, relative to the base directory.

        :param dir_path: path to new directory.
        """
        dir_complete_path = os.path.join(self.base_dir, dir_path)

        if os.path.exists(dir_complete_path):
            raise FileExistsError(dir_complete_path)

        os.makedirs(dir_complete_path)

    def serve_forever(self):
        """ Listens for new pushes forever """
        self.rpc_server.serve_forever()

    # --- END PUBLIC INTERFACE --- #

    def __save(self, file_complete_path, data):
        """
        Saves the data to the given file path.

        :param file_complete_path: the complete path where to store the data.
        :param data: data structure to be saved.
        """
        with open(file_complete_path, "wb") as unpatched:
            unpatched.seek(0)
            rsync.patchstream(unpatched, unpatched, data)


class PushServerInterface:
    """ Defines the public interface of the push server """

    def __init__(self, push_server):
        """
        Associates the push server interface with the given push server.

        :param push_server: server to associate with the interface.
        """
        self.push_server = push_server  # type: PushServer

    def push(self, file_path, data):
        """ see PushServer.push method """
        self.push_server.push(file_path, data)

    def push_dir(self, dir_path):
        """ see PushServer.push_dir method """
        self.push_server.push_dir(dir_path)
