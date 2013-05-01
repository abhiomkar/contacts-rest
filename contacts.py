# -*- coding: utf-8 -*-

# Author: Abhinay Omkar <abhiomkar@gmail.com>
# Contacts REST API

# Resources:
# /contact/<contact_id> - supported HTTP Methods GET, PUT, DELETE
# /contact - supported HTTP Methods POST (Create New) (post parameters: name, phone, email, location)
# /address_book - supported HTTP Methods GET (parameters: filter_byphone, filter_byname (searches on firstname, lastname or fullname), filter_bylocation, limit)

from flask import Flask, Response, request, make_response
from flask.ext import restful
from flask.ext.restful import reqparse, abort, output_json

import simplejson as json
import lxml.etree as xml
from lxml.etree import tostring
from collections import OrderedDict
import csv

app = Flask(__name__)
api = restful.Api(app)

class AddressBookData(OrderedDict):
    pass

class ContactData(OrderedDict):
    pass

address_book = AddressBookData()

def load_csv():
    """ Load data from CSV file to address_book - input file contacts.csv """
    global address_book
    address_book = AddressBookData()
    with open('contacts.csv', 'rb') as f:
       reader = csv.reader(f)
       for row in reader:
           contact_info = ContactData()
           contact_info['name'] = row[1].strip()
           contact_info['phone'] = row[2].strip()
           contact_info['email'] = row[3].strip()
           contact_info['location'] = row[4].strip()
           address_book[row[0].strip()] = contact_info

def write_to_csv(_dict):
    """ write address_book data to csv file - contacts.csv """
    rows = []

    for _id, _info in _dict.iteritems():
        row = []
        row.append(_id)
        for key, value in _info.items():
            row.append(value)
        rows.append(row)

    with open('contacts.csv', 'wb') as f:
        writer = csv.writer(f)
        writer.writerows(rows)

def abort_if_doesnt_exist(contact_id):
    if contact_id not in address_book.keys():
        abort(404, message="Contact id: {} doesn't exist".format(contact_id), status=404)

@api.representation('application/xml')
def output_xml(data, code, headers=None):
    print 'type:'
    print type(data)
    def contact_as_xml(contact):
        contact_id = contact.keys()[0]
        contact_info = contact.values()[0]

        contact_elem = xml.Element('contact')
        contact_elem.attrib['id'] = contact_id

        print 'contact_info:'
        print contact_info.items()
        for (tag, text) in contact_info.items():
            elem = xml.Element(str(tag))
            elem.text = str(text)
            contact_elem.append(elem)

        return contact_elem

    if isinstance(data, ContactData):
        # Contact data in xml
        xml_data = contact_as_xml(data)
    elif isinstance(data, AddressBookData):
        # AddressBook data in xml
        addressbook_elem = xml.Element('addressbook')
        for k, v in data.iteritems():
            addressbook_elem.append(contact_as_xml(ContactData({k: v})))
        xml_data = addressbook_elem
    else:
        # Any other data type
        print 'other data type'
        xml_data = xml.Element('root')
        for (tag, text) in data.items():
            elem = xml.Element(str(tag))
            elem.text = str(text)
            xml_data.append(elem)

    resp = make_response(tostring(xml_data, pretty_print=True), code)
    headers and resp.headers.extend(headers)
    return resp

@api.representation('application/json')
def output_json(data, code, headers=None):
    resp = make_response(json.dumps(data, indent=4*' '), code)
    headers and resp.headers.extend(headers)
    return resp

parser = reqparse.RequestParser()

# fields
parser.add_argument('name', type=str)
parser.add_argument('phone', type=int)
parser.add_argument('email', type=str)
parser.add_argument('location', type=str)

# options
parser.add_argument('limit', type=int)

# filter options
parser.add_argument('filter_byname', type=str)
parser.add_argument('filter_byphone', type=int)
parser.add_argument('filter_bylocation', type=str)


class Contact(restful.Resource):
    # READ
    def get(self, contact_id):
        abort_if_doesnt_exist(contact_id)
        return ContactData({contact_id: address_book[contact_id]})

    # DELETE
    def delete(self, contact_id):
        abort_if_doesnt_exist(contact_id)
        del address_book[contact_id]
        write_to_csv(address_book)

        return {'status': 204, 'message': 'Contact id: %s is deleted.' % contact_id}, 204

    # UPDATE
    def put(self, contact_id):
        abort_if_doesnt_exist(contact_id)

        args = parser.parse_args()
        contact = address_book[contact_id]

        for key, value in args.items():
            if value != None and contact.get(key, None):
                contact[key] = value

        address_book[contact_id] = contact
        write_to_csv(address_book)

        return {'status': 200, 'message': 'Contact id: %s is updated.' % contact_id}, 200

    # CREATE
    def post(self):
        args = parser.parse_args()
        contact = ContactData()
        contact_info = OrderedDict()

        new_id = int(max(map(int, address_book.keys()))) + 1

        for field in ['name', 'phone', 'email', 'location']:
            contact_info[field] = args.get(field, '')

        contact[new_id]=contact_info
        address_book.update(contact)
        print address_book
        write_to_csv(address_book)

        return {'status': 200, 'id': new_id, 'message': 'Contact id: %s is added.' % new_id}, 200

class AddressBook(restful.Resource):
    # READ - address book
    def get(self):

        self.limit = None

        args = parser.parse_args()
        self.filtered_contacts = address_book

        for key, value in args.items():

            if value == None:
                continue

            if key == 'limit':
                self.limit = value

            if key == 'filter_byname':
                return self._filter_by('name', value.strip())
            elif key == 'filter_byphone':
                return self._filter_by('phone', str(value).strip())
            elif key == 'filter_bylocation':
                return self._filter_by('location', value.strip())

        return address_book

    # AddressBook filter method
    def _filter_by(self, filter_type, filter_value):

        filtered_contacts = AddressBookData()

        for key, value in address_book.iteritems():

            if (self.limit != None) and (self.limit <= len(filtered_contacts.keys())):
                return filtered_contacts

            if filter_type == 'name':
                if len(filter_value.split()) > 1:
                    # if name filter has 2 or more words - Ex: search by full name
                    if value['name'].lower().startswith(filter_value.lower()):
                        filtered_contacts[key] = value
                else:
                    # if name filter has just one word - Ex: search by first name or last name
                    for name_part in value['name'].split():
                        if name_part.lower().startswith(filter_value.lower()):
                            filtered_contacts[key] = value
            elif filter_type == 'phone':
                if value['phone'] == filter_value:
                    filtered_contacts[key] = value
            elif filter_type == 'location':
                if value['location'].lower() == filter_value.lower():
                    filtered_contacts[key] = value

        return filtered_contacts

# Api resource routing

# Use Cases:
# - search address book (search by name (firstname or lastname), phone, location) GET
# - add new contact POST
# - update existing contact PUT
# - delete contact DELETE
# - get contact GET

api.add_resource(AddressBook, '/address_book')
api.add_resource(Contact, '/contact/<string:contact_id>', '/contact')

if __name__ == '__main__':
    load_csv()
    app.run(debug=True)
