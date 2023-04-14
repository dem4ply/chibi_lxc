#!/usr/bin/env python
# -*- coding: utf-8 -*-
from chibi.atlas import Chibi_atlas
from chibi.file import Chibi_path
import unittest
from chibi_lxc.container import Container, Not_exists_error


class Centos_test_without_mount( Container ):
    name = 'rocky_test_without_mounts'


class Centos_test( Container ):
    name = 'rocky_test'
    mounts = [
        "/home/dem4ply/mount/test /mnt/test/ none bind,create=dir 0 0",
        "/home/dem4ply/mount/test2 /mnt/test2/ none bind,create=dir 0 0"
    ]

class Centos_test_mount_with_envar( Container ):
    name = 'rocky_test'
    mounts = [
        "/home/$USER/mount/test /mnt/test/ none bind,create=dir 0 0",
        "/home/$USER/mount/test2 /mnt/test2/ none bind,create=dir 0 0"
    ]


class Test_mount( unittest.TestCase ):
    @classmethod
    def setUpClass( cls ):
        if not Centos_test.exists:
            Centos_test.create()
        Centos_test.provision()

    def test_when_dont_have_mounts_should_just_work( self ):
        self.assertFalse( Centos_test_without_mount.mounts )

    def test_mounts_should_be_a_chibi_atlas( self ):
        self.assertTrue( Centos_test.mounts )

    def test_property_mount_should_return_all_mounts( self ):
        self.assertTrue( Centos_test.mount )

    def test_mount_should_have_all_the_mounts( self ):
        self.assertTrue( Centos_test.mounts )
        mount = Centos_test.mount.entry
        for mount_entry in Centos_test.mounts:
            self.assertIn( mount_entry, mount )


class Test_mount_with_envars( unittest.TestCase ):
    @classmethod
    def setUpClass( cls ):
        if not Centos_test_mount_with_envar.exists:
            Centos_test_mount_with_envar.create()
        Centos_test_mount_with_envar.provision()

    def test_mount_should_have_all_the_mounts( self ):
        self.assertTrue( Centos_test_mount_with_envar.mounts )
        mount = Centos_test_mount_with_envar.mount.entry
        for mount_entry in Centos_test.mounts:
            self.assertIn( mount_entry, mount )
