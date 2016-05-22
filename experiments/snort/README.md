Benchmarking Snort in Different Isolation Systems Using TCPreplay
====================================================================

## Introduction

This experiment tests Snort using the same idealogy that we used for testing Suricata.

## Method

Same as Suricata test.

### Hardware

Same hardware as Suricata test, but on servers `cap14` (snort host) and `cap15` (tcpreplay host).

### Software

#### Suricata

Snort version:

```
        --== Initialization Complete ==--

   ,,_     -*> Snort! <*-
  o"  )~   Version 2.9.8.2 GRE (Build 335) 
   ''''    By Martin Roesch & The Snort Team: http://www.snort.org/contact#team
           Copyright (C) 2014-2015 Cisco and/or its affiliates. All rights reserved.
           Copyright (C) 1998-2013 Sourcefire, Inc., et al.
           Using libpcap version 1.7.4
           Using PCRE version: 8.35 2014-04-04
           Using ZLIB version: 1.2.8

           Rules Engine: SF_SNORT_DETECTION_ENGINE  Version 2.6  <Build 1>
           Preprocessor Object: SF_FTPTELNET  Version 1.2  <Build 13>
           Preprocessor Object: SF_POP  Version 1.0  <Build 1>
           Preprocessor Object: SF_SIP  Version 1.1  <Build 1>
           Preprocessor Object: SF_SSH  Version 1.1  <Build 3>
           Preprocessor Object: SF_GTP  Version 1.1  <Build 1>
           Preprocessor Object: SF_IMAP  Version 1.0  <Build 1>
           Preprocessor Object: SF_DCERPC2  Version 1.0  <Build 3>
           Preprocessor Object: SF_REPUTATION  Version 1.1  <Build 1>
           Preprocessor Object: SF_DNP3  Version 1.1  <Build 1>
           Preprocessor Object: SF_SSLPP  Version 1.1  <Build 4>
           Preprocessor Object: SF_DNS  Version 1.1  <Build 4>
           Preprocessor Object: SF_MODBUS  Version 1.1  <Build 1>
           Preprocessor Object: SF_SDF  Version 1.1  <Build 1>
           Preprocessor Object: SF_SMTP  Version 1.1  <Build 9>
```

and also uses the free version of [Emerging Rules](http://rules.emergingthreats.net/open/suricata/) as of TBA.

#### Trace files

We use the same `bigFlows.pcap` file for simplicity.

##### bigFlows.pcap

According to TCPreplay website, bigFlows.pcap has the following characteristics:

 > This is a capture of real network traffic on a busy private network's access point to the Internet. The capture is much larger and
 > has a smaller average packet size than the previous capture. It also has many more flows and different applications. If the large
 > size of this file isn't a problem, you may want to select it for your tests.
 > 
 > * Size: 368 MB
 > * Packets: 791615
 > * Flows: 40686
 > * Average packet size: 449 bytes
 > * Duration: 5 minutes
 > * Number Applications: 132

#### Performance Analysis

We analyze the performance of Snort from the statistics it prints _when exiting_.

### Test Setups

We still use the four setups, but just replace Suricata with Snort.

### Test cases

We have the following tests:

|     Setup     | Trace file    | Para. TCPreplays | Use VTAP? |  Memory* | CPU | Swappiness | Other Args           | Sample Size |
|:-------------:|:-------------:|:----------------:|:---------:|:--------:|:---:|:----------:|:--------------------:|:-----------:|
|   Bare metal  | bigFlows.pcap |       1          |     No    |   4 GB   |  4  |     5      | -                    |     30      |
|     Docker    | bigFlows.pcap |       1          |     No    |   2 GB   |  4  |     5      | -                    |     30      |
| Docker + vtap | bigFlows.pcap |       1          |    Yes    |   2 GB   |  4  |     5      | -                    |     30      |
|       VM      | bigFlows.pcap |       1          |    Yes    |   2 GB   |  4  |     5      | vCPUs=4              |     30      |
|   Bare metal  | bigFlows.pcap |       2          |     No    |   4 GB   |  4  |     5      | -                    |     30      |
|     Docker    | bigFlows.pcap |       2          |     No    |   2 GB   |  4  |     5      | -                    |     30      |
| Docker + vtap | bigFlows.pcap |       2          |    Yes    |   2 GB   |  4  |     5      | -                    |     30      |
|       VM      | bigFlows.pcap |       2          |    Yes    |   2 GB   |  4  |     5      | vCPUs=4              |     30      |
|   Bare metal  | bigFlows.pcap |       4          |     No    |   4 GB   |  4  |     5      | -                    |     30      |
|     Docker    | bigFlows.pcap |       4          |     No    |   2 GB   |  4  |     5      | -                    |     30      |
| Docker + vtap | bigFlows.pcap |       4          |    Yes    |   2 GB   |  4  |     5      | -                    |     30      |
|       VM      | bigFlows.pcap |       4          |    Yes    |   2 GB   |  4  |     5      | vCPUs=4              |     30      |

## Result

TBA.

## Conclusion

TBA.
