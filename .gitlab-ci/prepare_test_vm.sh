#!/usr/bin/env bash

/usr/share/ucs-school-import/scripts/create_ou DEMOSCHOOL
/usr/share/ucs-school-import/scripts/create_ou DEMOSCHOOL2

udm mail/domain create \
    --ignore_exists \
    --position "cn=domain,cn=mail,$(ucr get ldap/base)" \
    --set name="$(ucr get domainname)"

cat > /etc/ucsschool/kelvin/mapped_udm_properties.json <<__EOF__
    {
        "user": ["title"],
        "school_class": ["mailAddress"],
        "school": ["description"]
    }
__EOF__
univention-app restart ucsschool-kelvin-rest-api
cat > tests/test_server.yaml << __EOF__
host: $(hostname -f)
username: $(ucr get tests/domainadmin/username)
user_dn: $(ucr get tests/domainadmin/account)
password: $(ucr get tests/domainadmin/pwd)
__EOF__
