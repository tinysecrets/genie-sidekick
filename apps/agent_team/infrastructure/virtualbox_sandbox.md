# VirtualBox Sandbox

Use a VirtualBox VM on the HP Pavilion to execute untrusted code emitted by the
Coding Agent before it ever runs on a real machine.

## One-time VM creation

```bash
VBoxManage createvm --name "agent-sandbox" --ostype Ubuntu_64 --register
VBoxManage modifyvm "agent-sandbox" \
  --memory 4096 --cpus 2 --nic1 nat --audio none --usb off
VBoxManage createhd --filename ~/VirtualBox\ VMs/agent-sandbox/disk.vdi \
  --size 20480 --variant Standard
VBoxManage storagectl "agent-sandbox" --name SATA --add sata
VBoxManage storageattach "agent-sandbox" --storagectl SATA --port 0 --device 0 \
  --type hdd --medium ~/VirtualBox\ VMs/agent-sandbox/disk.vdi
```

Install a minimal Ubuntu Server inside, then snapshot it as `pristine`:

```bash
VBoxManage snapshot "agent-sandbox" take pristine
```

## Per-job lifecycle

```bash
# 1. Restore to pristine
VBoxManage snapshot "agent-sandbox" restore pristine

# 2. Boot headless
VBoxManage startvm "agent-sandbox" --type headless

# 3. ssh in, run the code emitted by the Coding Agent
ssh sandbox@127.0.0.1 -p 2222 'bash -s' < /tmp/job.sh

# 4. Tear down
VBoxManage controlvm "agent-sandbox" poweroff
```

The Pseudo Key for the Coding Agent is **never** copied into the sandbox.
Only the L3 Agent Key for the specific sidekick that owns the job is exposed,
and only via an ephemeral env var.
