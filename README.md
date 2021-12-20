## Install

> pip install -e .

> sudo env "PATH=$PATH" python -m packet_buddy.base

> sudo env "PATH=$PATH" python -m packet_buddy.old.impl

The repo contains two server-client bases for further development and tinkering. The initial complex version is in
the `packet_buddy.old` package and the newer simplified in the `packet_buddy.base`. The simplified client-server
solution allows easier extendability and tinkering by defining a `bytes_per_packet` option that can be used to implement
any kind of hiding in to data, by adding the respective protocols and converters into the server file.

The project could use more refactoring and code cleanup to provide a clear and extendable solution.

The protocol used here is designed as follows:

#### 32-Bit header

| 0000 | 0000 | 0000 0000 0000 0000 | 0000 0000 |
|------|------|---------------------|-----------|
| HEAD | TYPE |         ID          | DATA LEN  |

The protocol is embedded into the IP Timestamp Option, but it can be used in other cases too. The implementation appends
the IP timestamp option to the front of this header, namely the timestamp prelude
`01000100` followed by the length of the data block and a pointer to the next block after this one.

All in all it would look something like this (as defined in [RFC791](https://www.rfc-editor.org/rfc/rfc791.html)):

WORD 1 PRELUDE + LEN + PTR + OVERFLOW|FLAGS

WORD 2 HEADER

WORD 3 DATA

...

WORD X DATA

#### Message Transport

The data that is passed through the channel is encrypted and verified with `ChaCha20Poly1305`. Every message gets a
unique nonce from `os.urandom(12)`. The data is encrypted and then split into packets.

The data is transported with nonce first using the `TYPE` field with values `0010` for encryption and `0001` for data.

The head marks the first and last packets for current data frame by setting the `HEAD` to `1001` for start and `1010`
for end. Plain data transmission is marked with `1100`.

The `ID` field identifies a single transaction and provides `65,536` distinct values for each `ip-port` combo.
The `data len` field allows up to `256` words (`~1KB`) of data in a single packet.

The design is due to the limits in the IP Option size.

#### Example data embedding

This is how it can be used in IP Options or in ICMP payload:

```python
def icmp_wrap(target: str, data: bytes):
    time.sleep(0.5)
    return bytes(
        IP(
            dst=target,
            options=data
        ) / ICMP(type=3, code=3)
    )


def icmp_payload(target: str, data: bytes):
    time.sleep(0.5)
    return bytes(IP(dst=target) / ICMP(type=8) / data)
```

Usage in ICMP payload is a bit wasteful as the same kind of Option prelude is added here even though it is unnecessary.
If small refactors are done to the code it could be used to construct a more generalized solution with less waste.

#### Notes

The IP Option channel will not work due to packets with IP options getting dropped in many
cases [[1](https://www.stigviewer.com/stig/cisco_ios_router_rtr/2020-06-30/finding/V-96637),
[2](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2005/EECS-2005-24.pdf)]. It might work in LAN. The ICMP option is not
refined enough to be very useful as the data is echoed back, instead an error should be returned to not waste data.

Also, the program currently relies on a predefined encryption key which is insecure.