#!/usr/bin/env python



import sys
import pygtk
pygtk.require('2.0')

import gtk
import gtk.glade
import gnomeapplet
import gnome.ui
import os.path
import re
import gobject
import gc
import pysvn
import svn_applet_globals as pglobals
import xml.etree.ElementTree as ET

# Ubuntu Packages :
# apt-get install python-svn
# apt-get install python-elementtree



#-------------------------------------------------------------------------------
# Main class
#-------------------------------------------------------------------------------

class svnApplet(gnomeapplet.Applet):



    def gui_window_about(self, *arguments, **keywords):
        """ Show a Gnome About window
        """

        license = """
Gnome Subversion Applet
Copyright (C) 2008  Thomas Chemineau

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

        about = gtk.AboutDialog()
        about.set_name("Subversion Applet")
        about.set_version("0.1")
        about.set_license(license)
        about.set_wrap_license(True)
        about.set_website("https://projects.aepik.net/p/gnome-svn-applet/")
        about.set_authors(["Thomas Chemineau : Project Leader"])
        about.set_logo(self.logo)

        about.connect("response", self.handler_gui_window_about)
        about.show()

        #about = gnome.ui.About(
        #        "svn-applet",
        #        "0.1",
        #        "GPL",
        #        "Subversion Applet",
        #        ["Thomas Chemineau"],
        #        ["Thomas Chemineau"],
        #        "Thomas Chemineau",
        #        self.logo )
        #about.show()



    def gui_window_configure(self, *arguments, **keywords):
        """ Show the configuration window.
            The user will be able to choose directories to monitore, and ajust
            time of checking.
        """

        return



    def gui_window_refresh(self, *arguments, **keywords):
        """ Show a little window that ask for refreshing all svn checks.
        """

        refresh = gtk.MessageDialog(
                parent = None,
                flags = 0,
                type = gtk.MESSAGE_INFO,
                buttons = gtk.BUTTONS_OK + gtk.BUTTONS_CANCEL,
                message_format = "Checking all defined subversion directories ?"
            )

        refresh.set_default_response(gtk.RESPONSE_CANCEL)
        refresh.connect("response", self.handler_gui_window_refresh)
        refresh.show()



    def handler_timeout(self,event):
        """ Clock timer.
            This function checks if there is jobs to perform.
        """

        if self.check and not self.checkin:
            self.check = True
            self.check = False
            nb = self.svn_checkall()
            if nb != 0:
                self.set_icon(os.path.join(
                        pglobals.image_dir,'svn_applet_icon_24_active.png'))
            self.checkin = False

        return 1


    def handler_gui_window_about(self, window, response):
        """ This is the handler function of gui_window_about.
        """

        window.hide()
        window.destroy()



    def handler_gui_window_refresh(self, window, response):
        """ This is the handler function of gui_window_refresh.
            It is here where we decide to check or not all svn repositories.
        """

        window.hide()
        if response == gtk.RESPONSE_YES:
            self.check = True
        window.destroy()



    def handler_shutdown(self, event):
        """ Kill this applet
        """

        del self.applet



    def handler_ssl_server_trust_prompt(self, trust_dict):
        """ This function is an handler. Its job is to auto accept all
            non trusted certificates.
        """

        return True, trust_dict['failures'], False



    def read_configuration(self, path):
        """ Read an XML configuration file.
        """
        tree = ET.parse(path)

        directories = []
        for directory in tree.findall("directory"):
            directories.append(directory.text)

        return directories



    def set_icon(self, path):
        """ Update the applet icon.
        """

        self.icon.clear()
        gc.collect()
        self.icon_path = path
        self.icon.set_from_file(self.icon_path)



    def svn_check(self, directory):
        """ Check one SVN repository.
            Return a tuple (directory, local_rev, remote_rev)
        """

        client = pysvn.Client()
        client.callback_ssl_server_trust_prompt = self.handler_ssl_server_trust_prompt

        r_path, r_dict = client.info2(directory, recurse = False)[0]
        local_url = r_dict['URL']
        local_rev = r_dict['rev'].number

        #r_path, r_dict = client.info2(local_url, recurse = False)[0]
        #remote_rev = r_dict['rev'].number
        remote_rev = 10000

        return (r_path, local_rev, remote_rev)



    def svn_checkall(self):
        """ Check all SVN repositories.
            Thus function returns the number of SVN repositories to update.
        """

        directories_notUpdated = 0
        directories = self.read_configuration(
                os.path.join(pglobals.applet_dir,'/svn_applet.conf'))

        for directory in directories:
            r_path, l_rev, r_rev = self.svn_check(directory)
            if l_rev < r_rev:
                directories_notUpdated = directories_notUpdated + 1

        return directories_notUpdated



    def __init__(self, applet, iid):
        """ The main function.
            It is here where we build the applet and all graphical elements.
        """

        self.__gobject_init__()
        gnome.init(pglobals.name, pglobals.version)

        # Global internal parameters
        self.timeout_interval = 1000
        self.icon_path = ''
        self.check = False
        self.checkin = False

        # Build main images.
        # self.logo should be used for big image.
        # self.icon should be used as icon in Gnome Deskbar.
        self.logo = None
        self.logo = gtk.gdk.pixbuf_new_from_file(
                os.path.join(pglobals.image_dir,'svn_applet_icon.png'))
        self.icon = gtk.Image()
        self.set_icon(os.path.join(pglobals.image_dir,'svn_applet_icon_24.png'))
        self.icon.show()

        # This part describes the contains of the applet. We have a popup menu
        # when we click on the applet icon. Each items are associated with
        # a function which should show a particular window.
        propxml="""
			    <popup name="button3">
                <menuitem name="prefs" verb="Refresh" label="Force"
                        pixtype="stock" pixname="gtk-refresh" />
                <separator/>
                <menuitem name="prefs" verb="Preferences" label="Preferences"
                        pixtype="stock" pixname="gtk-properties" />
			    <menuitem name="about" verb="About" label="_About"
                        pixtype="stock" pixname="gtk-about"/>
			    </popup>"""
        verbs = [
                ("About", self.gui_window_about),
                ("Preferences", self.gui_window_configure),
                ("Refresh", self.gui_window_refresh)
            ]

        # Now, build the applet.
        self.hbox = gtk.HBox()
        self.hbox.pack_start(self.icon)
        self.applet = applet
        self.applet.add(self.hbox)
        self.applet.setup_menu(propxml, verbs, None)

        # The tooltips
        # This item print information when user point this icon applet.
        tooltips = gtk.Tooltips()
        tooltips.set_tip(applet, "Subversion Applet", tip_private=None)

        # Update info from filesystem.
        # We define the callback function for timer request.
        gobject.timeout_add(self.timeout_interval, self.handler_timeout, self)

        # Connecting the "destroy" signal and show the applet.
        applet.connect("destroy", self.handler_shutdown)
        applet.show_all()



gobject.type_register(svnApplet)



#-------------------------------------------------------------------------------
# Bonobo handler, for Gnome integration.
#-------------------------------------------------------------------------------

def svnAppletFactory(applet, iid):
    print "Building"
    svnApplet(applet,iid)
    return gtk.TRUE



#-------------------------------------------------------------------------------
# Main
#-------------------------------------------------------------------------------

if len(sys.argv) == 2 and sys.argv[1] == "debug":

    # Here, it is debug.

    main_window = gtk.Window(gtk.WINDOW_TOPLEVEL)
    main_window.set_title("Subversion Applet")
    main_window.connect("destroy", gtk.main_quit)
    app = gnomeapplet.Applet()
    svnAppletFactory(app, None)
    app.reparent(main_window)
    main_window.show_all()
    gtk.main()
    sys.exit()

else:

    # Normal functionnality.

    gnomeapplet.bonobo_factory(
            "OAFIID:GNOME_SvnApplet_Factory", 
            svnApplet.__gtype__,
            pglobals.name,
            pglobals.version,
            svnAppletFactory )

