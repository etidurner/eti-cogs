# LinkReplace (Red v3 Cog)

Resends only matched links with domain replacements in configured channels.

## Install

Add this folder to a Red cog path, then:

```
[p]load linkreplace
```

## Configure

```
[p]linkreplace channel add
[p]linkreplace rule add x.com xproxy.com
```

## Notes

- Only configured channels are monitored.
- Only matched link(s) are re-sent; the rest of the message is not reposted.
