import imaplib
import getpass
import os
import email

EMAIL_FOLDER = 'INBOX'
IMAP_SERVER = 'imap.yandex.ru'

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def pretty_print(message, klass=bcolors.OKGREEN):
    print klass + message + bcolors.ENDC


class MailReader(object):

    def __init__(self):
        self._mail = imaplib.IMAP4_SSL(IMAP_SERVER)

    def _login(self):
        login = raw_input("Yandex login: ")
        pwrd = getpass.getpass("Password: ")
        try:
            return self._mail.login(login, pwrd)
        except Exception as e:
            return 'ERROR', (e.message,)

    def login(self):
        while True:
            result, description = self._login()
            if result == 'OK':
                pretty_print('Login succesfull')
                return
            pretty_print('Login failed: ' + ' '.join(description), bcolors.FAIL)

    def get_emails_uids(self, folder):
        pretty_print('Selecting emails from server...', bcolors.OKBLUE)
        result, data = self._mail.select(folder)
        pretty_print("In email folder {} [{}] emails.".format(folder, next(iter(data), 0)))
        return self._mail.uid('search', None, "ALL")[1][0].split()

    def get_email_body(self, email_uids):
        print email_uids
        result, data = self._mail.uid('fetch', ','.join(email_uids), '(RFC822)')
        for header, raw_email in data[::2]:
            yield header.split('UID ', 1)[1].split(' ', 1)[0], raw_email


class MailParser(object):

    def __init__(self):
        self._folder = os.path.abspath(raw_input("Please input local folder for emails: "))
        pretty_print("Local folder: {}".format(self._folder), bcolors.OKBLUE)
        if not os.path.exists(self._folder):
            pretty_print("Folder '{}' doesn't exist, it will be created automaticaly".format(self._folder), bcolors.OKBLUE)
            os.makedirs(self._folder)

    def _local_email_file_name(self, uid):
        return uid + '.dat'

    def remove_email(self, uid):
        email_path = os.path.join(self._folder, self._local_email_file_name(uid))
        os.unlink(email_path)
        return uid

    def add_email(self, uid, content):
        email_path = os.path.join(self._folder, self._local_email_file_name(uid))
        with open(email_path, 'w') as email_file:
            email_file.write(content)

    def clear_non_existing(self, existing_uids):
        local_uids = self.get_local_email_uids()
        existing_set = set(existing_uids)
        removed = [self.remove_email(local_uid) for local_uid in local_uids if local_uid not in existing_set]
        if removed:
            pretty_print("Localy removed {} emails.".format(len(removed)), bcolors.OKBLUE)

    def get_local_email_uids(self):
        return (o.split('.', 1)[0] for o in os.listdir(self._folder) if '.dat' in o)

    def is_email_stored_localy(self, email_uid):
        return email_uid in self.get_local_email_uids()

    def read_email(self, uid):
        with open(os.path.join(self._folder, self._local_email_file_name(uid)), 'r') as email_file:
            return email_file.read()


def read_and_store_emails(mail_client, mail_parser, email_uids):
    mail_parser.clear_non_existing(email_uids)

    for email_uid, email_body in mail_client.get_email_body(
        [email_uid for email_uid in email_uids if not mail_parser.is_email_stored_localy(email_uid)]
    ):
        mail_parser.add_email(email_uid, email_body)

def main():   
    mail = MailReader()
    mail.login()
    email_uids = mail.get_emails_uids(EMAIL_FOLDER)

    mail_parser = MailParser()
    read_and_store_emails(mail, mail_parser, email_uids)
    email_uids = list(mail_parser.get_local_email_uids())
    for uid in email_uids:
        print email.message_from_string(mail_parser.read_email(uid))


if __name__ == '__main__':
    main()