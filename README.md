Flask App - Contacts REST API
-----------------------------

Contact Resource Test
=====================

	# Add New (CREATE)
	curl -X POST -d 'name=Alex&phone=1234567890&email=bryan@test.com&location=Canada' http://localhost:5000/contact
	echo -e '\nContact: _Alex_ should be created with the new id - with Response Code 200 \n'

	# Update existing contact (UPDATE)
	curl  -X PUT -H 'Accept: application/xml' -d 'phone=98765&email=aomkar@testing.com' http://localhost:5000/contact/1
	echo -e '\nContact id: 1 should be modified with the new data - with Response Code 200 (if not existed return 404)\n'

	# Delete existing contact (DELETE)
	curl -X DELETE 'http://localhost:5000/contact/6'
	echo -e '\nContact id: 6 should be deleted. (if not existed return 404 else return Response Code 204)\n'

	# get particular contact details (READ)
	curl 'http://localhost:5000/contact/2'
	echo -e '\nContact id: 2 details - with Response Code 200 (if not existed return 404)\n'

AddressBook Resource Test
=========================

	curl 'http://localhost:5000/address_book'
	echo -e '\nList all contacts in Address Book\n'

	curl 'http://localhost:5000/address_book?filter_byname=Bh'
	echo -e '\nonly contacts firstname or lastname starting with Bh\n'

	curl 'http://localhost:5000/address_book?filter_bylocation=Bangalore'
	echo -e '\nBangalore contacts only\n'

Content-Negotiation
===================

	curl -H 'Accept: application/xml' 'http://localhost:5000/contact/2'
	echo -e 'Contact details of id: 2 in XML format\n'

	# Contact doesn't exist
	curl -H 'Accept: application/xml' 'http://localhost:5000/contact/99999'
	echo -e 'Error message in xml format with Retrun Code 404\n'
