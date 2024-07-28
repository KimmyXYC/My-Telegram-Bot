# -*- coding: utf-8 -*-
# @Time: 2024/7/28 19:55
# @FileName: KeyboxBot.py
# @Software: PyCharm
# @GitHub: KimmyXYC
import aiohttp
import json
import tempfile
import xml.etree.ElementTree as ET
from loguru import logger
from datetime import datetime
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding


async def load_from_url():
    url = "https://android.googleapis.com/attestation/status"

    headers = {
        "Cache-Control": "max-age=0, no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f"Error fetching data: {response.status}")
            return await response.json()


def parse_number_of_certificates(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    number_of_certificates = root.find('.//NumberOfCertificates')

    if number_of_certificates is not None:
        count = int(number_of_certificates.text.strip())
        return count
    else:
        raise Exception('No NumberOfCertificates found.')


def parse_certificates(xml_file, pem_number):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    pem_certificates = root.findall('.//Certificate[@format="pem"]')

    if pem_certificates is not None:
        pem_contents = [cert.text.strip() for cert in pem_certificates[:pem_number]]
        return pem_contents
    else:
        raise Exception("No Certificate found.")


async def keybox_check(bot, message, document):
    file_info = await bot.get_file(document.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)

    with tempfile.NamedTemporaryFile(dir="downloads", delete=True) as temp_file:
        temp_file.write(downloaded_file)
        temp_file.flush()
        try:
            pem_number = parse_number_of_certificates(temp_file.name)
            pem_certificates = parse_certificates(temp_file.name, pem_number)
        except Exception as e:
            logger.error(f"[Keybox Check][message.chat.id]: {e}")
            await bot.reply_to(message, e)
            return
    try:
        certificate = x509.load_pem_x509_certificate(
            pem_certificates[0].encode(),
            default_backend()
        )
    except Exception as e:
        logger.error(f"[Keybox Check][message.chat.id]: {e}")
        await bot.reply_to(message, e)
        return

    # Certificate Validity Verification
    serial_number = certificate.serial_number
    serial_number_string = hex(serial_number)[2:].lower()
    reply = f"*Serial number:* `{serial_number_string}`"
    not_valid_before = certificate.not_valid_before
    not_valid_after = certificate.not_valid_after
    current_time = datetime.utcnow()
    is_valid = not_valid_before <= current_time <= not_valid_after
    if is_valid:
        reply += "\n✅ Certificate within validity period"
    elif current_time > not_valid_after:
        reply += "\n❌ Expired certificate"
    else:
        reply += "\n❌ Invalid certificate"

    # Keychain Authentication
    flag = True
    for i in range(pem_number - 1):
        son_certificate = x509.load_pem_x509_certificate(pem_certificates[i].encode(), default_backend())
        mother_certificate = x509.load_pem_x509_certificate(pem_certificates[i + 1].encode(), default_backend())

        if son_certificate.issuer != mother_certificate.subject:
            flag = False
            break
    if flag:
        for i in range(pem_number - 1):
            son_certificate = x509.load_pem_x509_certificate(pem_certificates[i].encode(), default_backend())
            mother_certificate = x509.load_pem_x509_certificate(pem_certificates[i + 1].encode(), default_backend())
            signature = son_certificate.signature
            signature_algorithm = son_certificate.signature_algorithm_oid._name
            tbs_certificate = son_certificate.tbs_certificate_bytes
            if signature_algorithm == 'sha256WithRSAEncryption':
                hash_algorithm = hashes.SHA256()
                padding_algorithm = padding.PKCS1v15()
            elif signature_algorithm == 'sha1WithRSAEncryption':
                hash_algorithm = hashes.SHA1()
                padding_algorithm = padding.PKCS1v15()
            elif signature_algorithm == 'sha384WithRSAEncryption':
                hash_algorithm = hashes.SHA384()
                padding_algorithm = padding.PKCS1v15()
            elif signature_algorithm == 'sha512WithRSAEncryption':
                hash_algorithm = hashes.SHA512()
                padding_algorithm = padding.PKCS1v15()
            else:
                raise ValueError("Unsupported signature algorithms")
            digest = hashes.Hash(hash_algorithm, backend=default_backend())
            digest.update(tbs_certificate)
            hash_value = digest.finalize()
            public_key = mother_certificate.public_key()
            try:
                public_key.verify(
                    signature,
                    hash_value,
                    padding_algorithm,
                    hash_algorithm
                )
            except Exception:
                flag = False
                break
    if flag:
        reply += f"\n✅ Effective key chain"
    else:
        reply += f"\n❌ Invalid keychain"

    # Validation of certificate revocation
    try:
        status_json = await load_from_url()
    except Exception:
        with open("res/json/status.json", 'r', encoding='utf-8') as file:
            status_json = json.load(file)
    status = status_json['entries'].get(serial_number_string, None)
    if status is None:
        reply += "\n✅ Serial number not found in Google's revoked keybox list"
    else:
        reply += f"\n❌ Serial number found in Google's revoked keybox list\n*Reason:* `{status['reason']}`"

    await bot.reply_to(message, reply, parse_mode='Markdown')
