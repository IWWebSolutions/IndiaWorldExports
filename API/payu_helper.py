# payu_helper.py
import hashlib

def generate_hash(data, salt):
    hash_sequence = "key|txnid|amount|productinfo|firstname|email|||||||||||"
    hash_string = '|'.join([str(data.get(field, '')) for field in hash_sequence.split('|')])
    hash_string += f'|{salt}'
    return hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()

def verify_hash(post_data, salt):
    received_hash = post_data.get('hash')
    hash_sequence = "key|txnid|amount|productinfo|firstname|email|||||||||||"
    reverse_hash_string = '|'.join([
        post_data.get('key', ''),
        post_data.get('txnid', ''),
        post_data.get('amount', ''),
        post_data.get('productinfo', ''),
        post_data.get('firstname', ''),
        post_data.get('email', ''),
        '', '', '', '', '', '', '', '', '', '', '', '', ''
    ])
    reverse_hash_string += f'|{salt}'
    generated_hash = hashlib.sha512(reverse_hash_string.encode('utf-8')).hexdigest().lower()
    return received_hash == generated_hash
