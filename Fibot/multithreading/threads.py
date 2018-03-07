#!/usr/bin/env python
# -*- coding: utf-8 -*-


#-- General imports --#
from threading import Timer
import datetime

#-- Local imports --#
from Fibot.Data.data_types.notification import Notification
from Fibot.api.api_raco import API_raco

class Notification_thread(object):

    """This class enables multithreading capabilities by using an extra thread to scan looking for
    notifications for users.

        Attributes:
            api(:class:`Fibot.api.api_raco.API_raco`): Object that accesses the info at Raco's API_raco
            message_handler(:class:`Fibot.message_handler.Message_handler`): Object that allows interaction with users
            delay(:obj:`int`): Amount of seconds between scans.
            thread(:class:`threading.Timer`): Thread that does the scanning.
            polling(:obj:`bool`): Object that indicates if polling has to be done
            last_check(:class:`datetime.datetime`): datetime of the last check for notifications
    """
    def __init__(self, mh, delay):
        self.api = API_raco()
        self.message_handler = mh
        self.chats = self.message_handler.chats
        self.delay = delay
        self.thread = None
        self.polling = True
        self.last_check = None

    """
        This function defines the new timer and starts it (effectively allows the scanning)
    """
    def run(self):
        print("Notification thread activated! Scanning every {} seconds".format(self.delay))
        if self.polling:
            self.thread = Timer(self.delay, self.poll)#, args = [self.chats, self.api])
            self.thread.start()

    """
        Does a scan over all users, and then returns to the activation function
    """
    def poll():#self, chats, api):
        print("Last check was done: {}".format(self.last_check))
        for student_id in self.chats.chats.keys():
            student = self.chats.get_chat(student_id)
            print("Checking chat_id {}".format(student_id))
            if student['notifications']:
                print("Scanning {}.".format(student['name']))
                access_token = student['access_token']
                avisos = self.api.get_avisos(access_token)
                avisos = self.filter(avisos)
                for avis in avisos:
                    message = Notification(avis).get_notif()
                    self.message_handler.send_message(student_id, message, typing=True)
                self.last_check = datetime.datetime.now()
        self.run()

    """
        Parameters:
            avisos(:obj:`list`): List of publications for a user

        This function filters the publications so that they were not sent previously.
    """
    def filter(self, avisos):
        for avis in avisos:
            avis_date = self.get_date(avis)
            if not self.last_check: yield avis
            elif avis_date > self.last_check: yield avis

    """
        Parameters:
            avis(:obj:`dict`): One publication

        This function returns the date of a publication. It also converts it to datetime.
        so it returns (:class:`datetime.datetime`)

        2018-03-01T00:00:00 -> datetime(year, month, day, hour, minute, second)
    """
    def get_date(self, avis):
        avis_date = avis['data_modificacio']
        avis_date_day, avis_date_hour = avis_date.split('T')
        year, month, day = avis_date_day.split('-')
        hour, minute, second = avis_date_hour.split(':')
        return datetime.datetime(int(year), int(month), int(day), int(hour), int(minute), int(second))

    """
        Allows polling
    """
    def stop_polling(self):
        self.polling = False

    """
        Forbids polling
    """
    def start_polling(self):
        self.polling = True