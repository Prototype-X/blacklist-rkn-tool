## Подписываем запрос на получение реестра запрещенных сайтов в формате PKCS#7 с использованием RuToken

## Системные требования: Ubuntu 14.04 64 bit + OpenSSL + OpenSC + Rutoken ECP

#### 1. Ubuntu 14.04 64 bit, доустанавливаем недостающее ПО

    apt-get install openssl libengine-pkcs11-openssl libccid libpcsclite1 libtool opensc pcscd

##### Включаем автостарт демона смарт-карт:

    sudo update-rc.d pcscd start

#### 2. Обеспечиваем поддержку в OpenSSL электронного ключа Aktiv Rutoken ECP

##### Скачиваем с сайта производителя библиотеки PKCS#11 и engine для OpenSSL 64 bit:

https://download.rutoken.ru/Rutoken/PKCS11Lib/1.3.2.0/Linux/x64/lib/librtpkcs11ecp.so
https://download.rutoken.ru/Rutoken/Support_OpenSSL/1.0/lin-x86_64/pkcs11_gost.so

~~Желательно не менять /etc/ssl/openssl.cnf использовать отдельный конфиг, который будет указан в параметрах или сделать вторую
установку openssl. В Debian после правки /etc/ssl/openssl.cnf ломался ssh, в Ubuntu таких проблем не возникает.~~

Добавляем в исходный файл /etc/ssl/openssl.cnf:

    # Extra OBJECT IDENTIFIER info:
    #oid_file               = $ENV::HOME/.oid
    oid_section             = new_oids
    openssl_conf            = openssl_def

    [openssl_def]
    engines                 = engine_section

    [engine_section]
    gost                    = gost_section
    pkcs11_gost             = pkcs11_section

    [gost_section]
    engine_id = gost
    dynamic_path = /usr/lib/x86_64-linux-gnu/openssl-1.0.0/engines/libgost.so
    default_algorithms      = ALL
    init = 0

    [pkcs11_section]
    engine_id = pkcs11_gost
    dynamic_path = /usr/lib/pkcs11-gost/pkcs11_gost.so
    MODULE_PATH = /usr/lib/pkcs11-gost/librtpkcs11ecp.so
    init = 0
    PIN                     = 12345678

Проверяем работоспособность engine openssl:

    root@zapret:/# openssl engine -v
    (rsax) RSAX engine support
    (dynamic) Dynamic engine loading support
         SO_PATH, NO_VCHECK, ID, LIST_ADD, DIR_LOAD, DIR_ADD, LOAD
    (gost) Reference implementation of GOST engine
         CRYPT_PARAMS
    (pkcs11_gost) pkcs11 gost engine
         SO_PATH, MODULE_PATH, VERBOSE, QUIET, PIN

Проверяем работоспособность электронного ключа:

    pkcs11-tool --module /usr/lib/pkcs11-gost/librtpkcs11ecp.so -Ol

Будет запрошен пин-код электронного ключа и выдан список объектов на ключе.

#### 3. Считываем с электронного ключа сертификат подписи

Среди объектов, хранящихся на электронном ключе нас интересуют сертификат и закрытый ключ (поле ID уникально для каждой тройки объектов: открытый ключ, закрытый ключ, сертификат):

    Certificate Object, type = X.509 cert
    label:      ViPNet Certificate
    ID:         1234567800000000123456789abcdef1

    Private Key Object; GOSTR3410
    PARAMS OID: 123456789123456789
    label:      ViPNet PrivateKey
    ID:         1234567800000000123456789abcdef1
    Usage:      decrypt, sign

Извлекаем сертификат, который будет использоваться для подписи, в файл cert.crt:

    pkcs11-tool --module /usr/lib/pkcs11-gost/librtpkcs11ecp.so -l -r -y cert -d 1234567800000000123456789abcdef1 -o cert.crt

В этой команде -d 1234567800000000123456789abcdef1 - ID сертификата.

#### 4. Преобразуем сертификат подписи из DER формата в PEM

    openssl x509 -in cert.crt -inform der -outform pem -out cert.pem

#### 5. Создаём электронную подпись

Имеется некий файл document.txt, для которого мы хотим создать электронную подпись.

Присоединённую:

    openssl smime -engine pkcs11_gost -sign -in document.txt \
    -out document.txt.attached.p7s -outform der -noverify -binary \
    -signer cert.pem -inkey 1234567800000000123456789abcdef1 \
    -keyform engine -nodetach

Отсоединённую:

    openssl smime -engine pkcs11_gost -sign -in document.txt \
    -out document.txt.detached.p7s -outform der -noverify -binary \
    -signer cert.pem -inkey 1234567800000000123456789abcdef1 \
    -keyform engine

Поле -inkey 1234567800000000123456789abcdef1 определяет ID закрытого ключа, использующегося при создании подписи.

На выходе получаем файлы: document.txt.detached.p7s, который содержит электронную подпись файла document.txt, и document.txt.attached.p7s, который содержит текст документа + его электронную подпись.

#### 6. Проверяем электронные подписи

Присоединённую:

    openssl smime -verify -in document.txt.attached.p7s -noverify -inform der

Отсоединённую:

    openssl smime -verify -in document.txt.attached.p7s -noverify -inform der -content document.txt

Примечание:
Во всех командах openssl используется параметр -noverify - не происходит автоматическая проверка сертификата подписи на валидность.

#### Дополнительная информация

##### Проверяем период действия сертификата:

    openssl x509 -noout -in cert.pem -dates
    notBefore=Jan 22 10:04:05 2014 GMT
    notAfter=Jan 22 10:04:05 2015 GMT

    openssl x509 -noout -in cert.pem -text

##### Сборка OpenSSL 1.0.1p c libgost.so

    wget https://github.com/openssl/openssl/archive/OpenSSL_1_0_1p.tar.gz
    tar xzf openssl-1.0.1p.tar.gz
    cd openssl-1.0.1p
    make clean
    make dclean
    ./config -fPIC shared zlib enable-rfc3779 --prefix=/usr/local
    make depend
    make all
    make tests
    sudo make install

Источники:

[www.cainet.ru](http://www.cainet.ru/content/pkcs7sign)

[info.ssl.com](http://info.ssl.com/article.aspx?id=12149)

[RuToken forum](http://forum.rutoken.ru/topic/1639/page/13/)
