import configparser
import os, inspect

folder = os.path.realpath(os.path.abspath(os.path.split(inspect.getfile(inspect.currentframe()))[0]))

MACROFILE = "macros.ini"


class Macro:
    """
    Class representing a G Code Macro

    Attributes:
        name - the name of the macro as it will appear on buttons, etc
        tag - the suffix given when macros are loaded - provides a sort sequence
        section - the section of the ini file that this macro came from
        commands - a list of the G Code commands that this macro will send
    """
    def __init__(self, name, tag, commands, sect="global"):
        """
        Constructor

        Parameters:
            same as above, section has a default value of global
        """
        self.name = name
        self.tag = tag
        self.commands = commands
        self.section = sect

    def setCommands(self, cmds):
        """
        set the command string array for this macro
        """
        self.commands = cmds

    def getCommands(self):
        """
        retrieve the command string array for this macro
        """
        return self.commands

    def getName(self):
        """
        retrieve the name for this macro
        """
        return self.name

    def setTag(self, tag):
        """
        set the tag for this macro
        """
        self.tag = tag

    def getTag(self):
        """
        set the tag feveor this macro
        """
        return self.tag

    def setSection(self, sect):
        """
        set the section name for this macro
        """
        self.section = sect

    def getSection(self):
        """
        retrieve the section name for this macro
        """
        return self.section


class MacroList:
    """
    MacroList: load and manage macros

    attributes:
        fn - the filename containing the macro definiitons
        pname - the printer name
        c - the ConfigParser object that parses the file
        macroList - a dictionary relating macro name to Macro object
        tags - a dictionary relating macro name to tag - used for sorting
        orderList - a list of macro objects ordered by tag value
    """
    def __init__(self, pname):
        """
        Constructor - printer name
        """
        self.inifile = os.path.join(folder, MACROFILE)
        self.pname = pname
        self.c = configparser.ConfigParser()
        self.c.read(self.inifile)

        self.macroList, self.tags = self.__getMacros("global")
        macroList, tags = self.__getMacros(pname)

        self.macroList.update(macroList)
        self.tags.update(tags)

        self.orderList = [key for key, _ in sorted(self.tags.items(), key=lambda x: x[1])]

    def findMacroByName(self, name):
        """
        findMacroByName - return the Macro object related to name
        returns Macro object - None if name does not exist
        """
        try:
            return self.macroList[name]
        except IndexError:
            return None

    def getOrderedList(self):
        """
        getMacroList
        returns a list of Macro objects ordered by tag values
        """
        return [self.macroList[x] for x in self.orderList]

    def __getMacros(self, sect):
        """
        __getMacros - an internal routine to parse the configparser file and load macros
        """
        macroList = {}
        tags = {}
        if not self.c.has_section(sect):
            return macroList, tags

        for tag, value in self.c.items(sect):
            if tag.startswith("name."):
                index = tag.split('.', 1)[1]
                opt = "macro.%s" % index

                try:
                    macro = self.c.get(sect, opt)
                except configparser.NoOptionError:
                    print("Macro for name %s(%s) is missing" % (tag, value))
                    continue

                cmds = macro.split(';')
                if value in macroList.keys():
                    macroList[value].setCommands(cmds)
                    macroList[value].setTag(index)
                    macroList[value].setSection(sect)
                else:
                    macroList[value] = (Macro(value, index, cmds, sect))
                    tags[value] = index

        return macroList, tags

