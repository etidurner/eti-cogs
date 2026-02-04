# LinkReplace

Checks messages for domains in links and, based on the configured rules, resends the link with a different chosen domain.

## Install

Add this repository, if not added already:
```
[p]repo add eti-cogs https://github.com/etidurner/eti-cogs
```
Install the cog:
```
.cog install eti-cogs linkreplace
```
Load the cog:
```
.load linkreplace
```

## Configure

Add a channel to monitor:
```
[p]linkreplace channel add #channelName
```

Add a rule for a domain to replace:
```
[p]linkreplace rule add x.com xcancel.com
```

## Notes

- Only configured channels are monitored.
