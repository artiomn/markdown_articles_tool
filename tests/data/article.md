# Установка Debian с корнем на шифрованном ZFS зеркале

![image](img/lolcat-techsupport.jpg)


## Предисловие

В связи с необходимостью работать в другом городе, пришлось приобрести ноутбук.
Постепенно, назрела проблема синхронизации его и стационарной машины.
Несмотря на то, что все мои проекты ведутся в гите, не весь код полностью мой, и не хочется его выкладывать на гитхаб.

Для решения этой проблемы, я начал строить свой NAS, который даст мне, ко всему прочему, дополнительные возможности.

Изучив, какие сейчас имеются ОС для решения данной задачи, я пришёл к выводу, что изо всего многообразия, наиболее развиты, широко используемы и, следовательно, проработаны, [FreeNAS](freenas.org) на основе FreeBSD и [OpenMediaVault](www.openmediavault.org) на основе Debian, созданный одним из разработчиков FreeNAS.

FreeNAS стабилен, удобен, гибок и вообще хорош, но попытавшись его поставить, вместо FreeBSD bsdinstall, я увидел совершенно урезанный инсталлятор, в котором я могу только выбрать диски и ввести пароль root: даже разметить диски нельзя.
GELI мне понравился больше cryptsetup на Linux, как и BSD-шный parted.
Попытавшись сделать root на шифрованном разделе, я понял, что эта задача нетривиальна, несмотря на то, что они уже используют root на ZFS.
Затем, пообщавшись, с сообществом FreeNAS, которые стали доказывать, что FreeNAS - не ОС, а приложение, я решил установить OMV.

К тому же, Debian - моя основная ОС и с Linux дела обещали быть проще...

Выяснилось, что не совсем. Задача создания такой конфигурации, как у меня, совсем не тривиальна. Потому, я решил написать данную статью.
<cut/>


## Существующие ресурсы

[Руководство проекта ZFS for Linux](https://github.com/zfsonlinux/zfs/wiki/Debian-Stretch-Root-on-ZFS) - основной документ, без которого мне пришлось бы разбираться гораздо дольше.
Его необходимо хотя бы кратко посмотреть.

Выполнив большую часть работы вручную, я наткнулся на [скрипт](https://github.com/arcenik/debian-zfs-root/blob/master/d8zlroot.sh) выполняющий сходную задачу, но без организации зеркала.

Ну и, всё же упомяну здесь man по cryptsetup, [руководство Debian по шифрованию](https://wiki.debian.org/ru/Crypt), [статьи и документацию по ZFS](http://xgu.ru/wiki/ZFS) (там есть ссылки на оригинальную документацию).

Много данных по ZFS есть на [форуме FreeNAS](https://forums.freenas.org/index.php).

И уже в процессе написания данной статьи, выяснилось, что [ничто не ново под Луной](https://thestaticvoid.com/post/2013/10/26/how-i-do-encrypted-mirrored-zfs-root-on-linux/).

Однако, моя несколько схема другая, и она имеет, как свои недостатки, так и преимущества.


## Схема организации диска

Система установлена на двух SSD: Micron и Samsung PRO (в дальнейшем, я буду к ним обращаться).

На каждой SSD такая схема разбиения:

- `part_boot` - раздел с загрузчиком. Размер = 1 GB.
- `part_system` - раздел с системой. Размер = 32 GB (Рекомендованный размер: 16 GB * 2).
- `part_slog` - раздел с SLOG. Размер = 5 GB.

`part_system` и `part_slog` зашифрованы в XTS режиме.

В целом, выглядит это так:

```
SSD1: [part_boot] -> [ext4] <---> SSD2
SSD1: [part_system] -> [crypto_xts] -> [zfs_mirror] <---> SSD2
SSD1: [part_slog] -> [crypto_xts] -> [zfs_zil_mirror] <---> SSD2
```

ZIL и корень системы дублируются на вторую SSD средствами ZFS.


## Подготовка

1. [Загрузить ISO Debian](https://cdimage.debian.org/debian-cd/current-live/amd64/iso-hybrid/).
2. Установить образ на USB flash.


## Установка

Дальнейшие действия во много заимствованы из [руководства](https://github.com/zfsonlinux/zfs/wiki/Debian-Stretch-Root-on-ZFS) и даны с некоторыми моими пояснениями.
Предполагается, что все команды выполняются от root.


### Добавить contrib в sources.list, что требуется для установки ZFS

`echo "deb http://ftp.debian.org/debian stretch main contrib" > /etc/apt/sources.list && apt-get update`


### Установить debootstrap и zfs-dkms

`apt-get install debootstrap linux-headers-$(uname -r) zfs-dkms`


### Установить cryptsetup

`apt-get install cryptsetup`

### Забить SSD случайными данными

`dd if=/dev/urandom bs=4M oflag=direct of=/dev/disk/by-id/ata-Samsung_SSD_850_PRO && blkdiscard /dev/disk/by-id/ata-Samsung_SSD_850_PRO`
`dd if=/dev/urandom bs=4M oflag=direct of=/dev/disk/by-id/ata-Micron_1100 && blkdiscard /dev/disk/by-id/ata-Micron_1100`

Это займёт порядка 30 минут для SSD размером 250 ГБ.
Вызов blkdiscard пометит все блоки на SSD, как неиспользуемые.


### Создать разделы для загрузки

`sgdisk -a1 -n1:34:2047 -t1:EF02 -n2:0:+1G -t2:8300 /dev/disk/by-id/ata-Samsung_SSD_850_PRO`
`sgdisk -a1 -n1:34:2047 -t1:EF02 -n2:0:+1G -t2:8300 /dev/disk/by-id/ata-Micron_1100`

Сюда, впоследствии будет установлен GRUB.
**Создание первого маленького раздела обязательно: без него не загрузится.**


### Создать системные разделы

`sgdisk -n3::+32G -t3:8300 -c3:part_system1 /dev/disk/by-id/ata-Samsung_SSD_850_PRO`
`sgdisk -n3::+32G -t3:8300 -c3:part_system2 /dev/disk/by-id/ata-Micron_1100`


### Создать разделы SLOG

`sgdisk -n4::+5G -t4:8300 -c4:part_slog1 /dev/disk/by-id/ata-Samsung_SSD_850_PRO && sgdisk -n4::+5G -t4:8300 -c4:part_slog2 /dev/disk/by-id/ata-Micron_1100`

В этой статье, они никак не используются.


### Создать шифрованные корневые разделы

Стоит это делать [руководствуясь документом от Debian](https://wiki.debian.org/ru/Crypt), если вы не очень хорошо знаете cryptsetup.
Здесь используется LUKS, что несколько упрощает работу с шифрованием.

`cryptsetup --cipher aes-xts-plain64 --key-size 512 --verify-passphrase --hash sha512 --use-random -v luksFormat /dev/disk/by-id/ata-Samsung_SSD_850_PRO-part3`
`cryptsetup --cipher aes-xts-plain64 --key-size 512 --verify-passphrase --hash sha512 --use-random -v luksFormat /dev/disk/by-id/ata-Micron_1100-part3`

Теперь надо открыть разделы:

`cryptsetup luksOpen /dev/disk/by-id/ata-Samsung_SSD_850_PRO-part3 root_crypt1`
`cryptsetup luksOpen /dev/disk/by-id/ata-Micron_1100-part3 root_crypt2`

После ввода корректного пароля, будут созданы новые блочные устройства, которые используются для шифрования.
На них разместится корневой пул ZFS.


### Создать корневой ZFS pool

      modprobe zfs
      zpool create -o ashift=12 \
        -O atime=off -O canmount=off -O compression=lz4 -O normalization=formD \
        -O mountpoint=/ -R /mnt \
        rpool mirror /dev/disk/by-id/dm-name-root_crypt*

Теперь есть пул, в который входят оба шифрованных раздела, включенные зеркально.

<spoiler title="Примечание о параметре ashift">
`ashift` - степень, в которую надо возвести двойку, чтобы получить указанный размер блока.
12 - это блок 4K.
Получить размер блока возможно командой `blockdev --getbsz /dev/<disk>`, либо из технической спецификации на устройство.
Если размер блока не соответствует размеру сектора диска, будет просадка производительности.
Современные жёсткие диски имеют размер сектора в 4K и эмуляцию сектора 512 байт.
За исключением высокооборотистых SAS дисков низкого объёма (порядка сотен ГБ), размер сектора которых остаётся 512 байт.
</spoiler>


### Создать наборы данных для корневой ФС

`zfs create -o canmount=off -o mountpoint=none rpool/ROOT`
`zfs create -o canmount=noauto -o mountpoint=/ rpool/ROOT/debian`


### Сделать корень загрузочным

`zfs mount rpool/ROOT/debian`
`zpool set bootfs=rpool/ROOT/debian rpool`


### Создать прочие наборы данных

`zfs create                 -o setuid=off              rpool/home`
`zfs create -o mountpoint=/root                        rpool/home/root`
`zfs create -o canmount=off -o setuid=off  -o exec=off rpool/var`
`zfs create -o com.sun:auto-snapshot=false             rpool/var/cache`
`zfs create                                            rpool/var/log`
`zfs create                                            rpool/var/spool`
`zfs create -o com.sun:auto-snapshot=false -o exec=on  rpool/var/tmp`

**На данном этапе, структура ФС готова.**


### Установить минимальную систему

`chmod 1777 /mnt/var/tmp`
`debootstrap stretch /mnt && zfs set devices=off rpool`


### Сконфигурировать систему

`echo nas > /mnt/etc/hostname`.
`echo "rpool/ROOT/debian / zfs defaults,noatime 0 0" > /mnt/etc/fstab`
`echo "tmpfs /tmp tmpfs nosuid,nodev 0 0" >> /mnt/etc/fstab`

Здесь /tmp монтируется, как tmpfs, а / будет на ZFS.
Затем, надо исправить `/mnt/etc/hosts`. В него требуется добавить имя хоста "nas".
И добавить настройки сетевых интерфейсов в `/mnt/etc/network/interfaces.d` (обязательно):
    - iface_name - имя активного интерфейса в `ip addr show`.
    - `echo "auto $iface_name" > /mnt/etc/network/interfaces.d/$iface_name`
    - `echo "iface $iface_name inet dhcp" >> /mnt/etc/network/interfaces.d/$iface_name`

*Это важный пункт!* Если этого не сделать, после перезагрузки вы окажетесь без сети и без установленных пакетов. Не сделаете - сеть всё-равно придётся поднимать вручную.


### Переключиться в установленную систему

`mount --rbind /dev /mnt/dev &&  mount --rbind /proc /mnt/proc && mount --rbind /sys /mnt/sys`
`chroot /mnt /bin/bash --login`
`mount /tmp`

*Далее, вся работа идёт в установленной системе*.

### Настроить APT и установить нужные пакеты

- Установить пакет HTTPS транспорта: `apt-get install apt-transport-https`
  Опционально, но я предпочитаю работать через HTTPS.
- Добавить репозиторий contrib:
    cat > /etc/apt/sources.list << EOF
    deb https://deb.debian.org/debian stretch main contrib
    deb-src https://deb.debian.org/debian stretch main contrib
    EOF
- `apt-get update`.
- Установить необходимые пакеты:
  - `apt-get install locales && dpkg-reconfigure locales`
  - `dpkg-reconfigure tzdata`
  - `apt-get install bash-completion man gdisk linux-headers-$(uname -r) linux-image-amd64`
  - `apt-get install cryptsetup zfs-dkms zfs-initramfs`

Сборка модуля ZFS займёт ощутимое время.


### Настроить cryptsetup

Безусловно включить в initramfs:
`sed -i 's/#CRYPTSETUP=/CRYPTSETUP=y/' /etc/cryptsetup-initramfs/conf-hook`

Затем, надо исправить хук cryptroot в /usr/share/initramfs-tools/hooks/cryptroot и заменить скрипт в /etc/initrmafs-tools/scripts/local-top/cryptroot.
Существуют две проблемы с пакетом cryptsetup в Debian Stretch:
- Он не работает с ZFS.
- При загрузке, он не кэширует вводимый пароль.

Баг на ZFS уже давно заведён, туда отправлены и мои доработки.
На кэширование пароля я завёл баг и отправил фикс, так что, возможно он уже будет исправлен.

Тем не менее, я привожу полные скрипты и диффы:
<spoiler title="/usr/share/initramfs-tools/hooks/cryptroot">
```bash
#!/bin/sh

PREREQ=""

prereqs()
{
	echo "$PREREQ"
}

case $1 in
prereqs)
	prereqs
	exit 0
	;;
esac

. /usr/share/initramfs-tools/hook-functions

# get_fs_devices() - determine source device(s) of mount point from /etc/fstab
#
# expected arguments:
# * fstab mount point (full path)
#
# This function searches for the first entry from /etc/fstab which has the
# given mountpoint set. It returns the canonical_device() of corresponding
# source device (first field in /etc/fstab entry).
# In case of btrfs, canoncial_device() of all btrfs source devices (possibly
# more than one) are returned.
#
get_fs_devices() {
	local device mount type options dump pass
	local wantmount="$1"

	if [ ! -r /etc/fstab ]; then
		return 1
	fi

	grep -s '^[^#]' /etc/fstab | \
	while read device mount type options dump pass; do
		if [ "$mount" = "$wantmount" ]; then
			local devices
			if [ "$type" = "btrfs" ]; then
				for dev in $(btrfs filesystem show $(canonical_device "$device" --no-simplify) 2>/dev/null | sed -r -e 's/.*devid .+ path (.+)/\1/;tx;d;:x') ; do
					devices="${devices:+$devices }$(canonical_device "$dev")"
				done
                      elif [ "$type" = "zfs" ]; then
                              zpool="$(echo "$device"|sed 's#^/dev/zvol/##;s#\([^/]*\).*#\1#')"
                              for ss in $(zpool list -Pv "$zpool"); do
                                      cdev=$(canonical_device "$ss" 2>/dev/null) || continue
                                      devices="${devices:+$devices }$cdev"
                              done || return 0
			else
				devices=$(canonical_device "$device") || return 0
			fi
			printf '%s' "$devices"
			return
		fi
	done
}

# get_resume_devices() - determine devices used for system suspend/hibernate
#
# expected arguments:
# * none
#
# This function searches well known places for devices that are used for system
# suspension and/or hibernation. It returns canonical_device() of any detected
# devices and prints a warning if more than one device is detected.
#
get_resume_devices() {
	local device opt count dupe candidates devices derived
	candidates=""

	# First, get a list of potential resume devices

	# uswsusp
	if [ -e /etc/uswsusp.conf ]; then
		device=$(sed -rn 's/^resume device[[:space:]]*[:=][[:space:]]*// p' /etc/uswsusp.conf)
		if [ -n "$device" ]; then
			candidates="${candidates:+$candidates }$device"
		fi
	fi

	# uswsusp - again...
	if [ -e /etc/suspend.conf ]; then
		device=$(sed -rn 's/^resume device[[:space:]]*[:=][[:space:]]*// p' /etc/suspend.conf)
		if [ -n "$device" ]; then
			candidates="${candidates:+$candidates }$device"
		fi
	fi

	# regular swsusp
	for opt in $(cat /proc/cmdline); do
		case $opt in
			resume=*)
				device="${opt#resume=}"
				candidates="${candidates:+$candidates }$device"
				;;
		esac
	done

	# initramfs-tools >=0.129
	device="${RESUME:-auto}"
	if [ "$device" != none ]; then
		if [ "$device" = auto ]; then
			# next line from /usr/share/initramfs-tools/hooks/resume
			device="$(grep ^/dev/ /proc/swaps | sort -rnk3 | head -n 1 | cut -d " " -f 1)"
			if [ -n "$device" ]; then
				device="UUID=$(blkid -s UUID -o value "$device" || true)"
			fi
		fi
		candidates="${candidates:+$candidates }$device"
	fi

	# Now check the sanity of all candidates
	devices=""
	count=0
	for device in $candidates; do
		# Remove quotes around device candidate
		device=$(printf '%s' "$device" | sed -r -e 's/^"(.*)"\s*$/\1/' -e "s/^'(.*)'\s*$/\1/")

		# Weed out clever defaults
		if [ "$device" = "<path_to_resume_device_file>" ]; then
			continue
		fi

		# Detect devices required by decrypt_derived
		derived=$(get_derived_device "$device")
		if [ -n "$derived" ]; then
			devices="${devices:+$devices }$derived"
		fi

		device=$(canonical_device "$device") || return 0

		# Weed out duplicates
		dupe=0
		for opt in $devices; do
			if [ "$device" = "$opt" ]; then
				dupe=1
			fi
		done
		if [ $dupe -eq 1 ]; then
			continue
		fi

		# This device seems ok
		devices="${devices:+$devices }$device"
		count=$(( $count + 1 ))
	done

	if [ $count -gt 1 ]; then
		echo "cryptsetup: WARNING: found more than one resume device candidate:" >&2
		for device in $devices; do
			echo "                     $device" >&2
		done
	fi

	if [ $count -gt 0 ]; then
		printf '%s' "$devices"
	fi

	return 0
}

# get_initramfs_devices() - determine devices with explicit 'initramfs' option
#
# expected arguments:
# * none
#
# This function processes entries from /etc/crypttab with the 'initramfs'
# option set. For each processed device, potential get_derived_device()
# devices are determined. The canonical_device() of each detected device
# is returned.
#
get_initramfs_devices() {
	local device opt count dupe target source key options candidates devices derived

	candidates="$(grep -s '^[^#]' /etc/crypttab | \
	while read target source key options; do
		if printf '%s' "$options" | grep -Eq "^(.*,)?initramfs(,.*)?$"; then
			echo " /dev/mapper/$target"
		fi
	done;)"

	devices=""
	count=0
	for device in $candidates; do
		# Detect devices required by decrypt_derived
		derived=$(get_derived_device "$device")
		if [ -n "$derived" ]; then
			devices="${devices:+$devices }$derived"
		fi

		device=$(canonical_device "$device") || return 0

		# Weed out duplicates
		dupe=0
		for opt in $devices; do
			if [ "$device" = "$opt" ]; then
				dupe=1
			fi
		done
		if [ $dupe -eq 1 ]; then
			continue
		fi

		# This device seems ok
		devices="${devices:+$devices }$device"
		count=$(( $count + 1 ))
	done

	if [ $count -gt 0 ]; then
		printf '%s' "$devices"
	fi

	return 0
}

# get_derived_device() - determine dependency devices for decrypt_derived
#
# expected arguments:
# * crypttab target device name (either <name> or /dev/mapper/<name>)
#
# This function takes a target device name and checks whether this device has
# the decrypt_derived keyscript set in /etc/crypttab. If true, the dependency
# device required for the decrypt_derived keyscript is detected and its
# canonical_device() returned if it's not listed in $rootdevs.
#
get_derived_device() {
	local device derived
	device="$1"

	derived="$( awk -vtarget="${device#/dev/mapper/}" \
		'$1 == target && $4 ~ /^(.*,)?keyscript=([^,]*\/)?decrypt_derived(,.*)?$/ {print $3; exit}' \
		/etc/crypttab )"
	if [ -n "$derived" ]; then
		if node_is_in_crypttab "$derived"; then
			derived=$(canonical_device "/dev/mapper/$derived") || return 0
			if ! printf '%s' "$rootdevs" | tr ' ' '\n' | grep -Fxq "$derived"; then
				printf '%s' "$derived"
			fi
		else
			echo "cryptsetup: WARNING: decrypt_derived device $derived not found in crypttab" >&2
		fi
	fi
}

# node_is_in_crypttab() - test whether a device is configured in /etc/crypttab
#
# expected arguments:
# * crypttab target device names (without /dev/mapper/ prefix)
#
# This function takes a target device name and fails if it is not
# configured in /etc/crypttab.
#
node_is_in_crypttab() {
	[ -f /etc/crypttab ] || return 1
	sed -n '/^[^#]/ s/\s.*//p' /etc/crypttab | grep -Fxq "$1"
}

# node_or_pv_is_in_crypttab() - test whether devices are configured in /etc/crypttab
#
# expected arguments:
# * crypttab target device names (without /dev/mapper/ prefix), or LVM
#   logical volume device-mapper name (format <VG>-<LV>)
#
# This function fails unless every argument is either a target device
# name configured in /etc/crypttab, or an LVM logical volume
# device-mapper name (format <VG>-<LV>) with only parents devices (PVs)
# configured in /etc/crypttab.
#
node_or_pv_is_in_crypttab() {
	local node lvmnodes lvmnode
	for node in "$@"; do
		if ! node_is_in_crypttab "$node"; then
			lvmnodes="$(get_lvm_deps "$node" --assert-crypt)" || return 1
			[ "$lvmnodes" ] || return 1
			for lvmnode in $lvmnodes; do
				node_is_in_crypttab "$lvmnode" || return 1
			done
		fi
	done
	return 0
}

# get_lvm_deps() - determine the parent devices (PVs) of a LVM logical volume
#
# expected arguments:
# * LVM logical volume device-mapper name (format <VG>-<LV>)
# * optional options to the function
#
# This function takes a LVM logical volume name and determines the corresponding
# crypted physical volumes (PVs). It returns the name of the underlying
# device-mapper crypt devices (without /dev/mapper).
# If option '--assert-crypt' is given as second argument, then the
# function fails unless all PVs are dm-crypt devices.
#
get_lvm_deps() {
	local node opt deps maj min depnode
	node="$1"
	opt="${2:-}"

	if [ -z "$node" ]; then
		echo "cryptsetup: WARNING: get_lvm_deps - invalid arguments" >&2
		return 1
	fi

	if ! deps=$(vgs --noheadings -o pv_name $(dmsetup --noheadings splitname $node | cut -d':' -f1) 2>/dev/null); then
		# $node is not a LVM node, stopping here
		[ "$opt" != '--assert-crypt' ] && return 0 || return 1
	fi

	# We should now have a list of physical volumes for the VG
	for dep in $deps; do
		depnode=$(dmsetup info -c --noheadings -o name "$dep" 2>/dev/null)
		if [ -z "$depnode" ]; then
			[ "$opt" != '--assert-crypt' ] && continue || return 1
		fi
		if [ "$(dmsetup table "$depnode" 2>/dev/null | cut -d' ' -f3)" != "crypt" ]; then
			get_lvm_deps "$depnode" $opt || return 1
			continue
		fi
		printf '%s\n' "$depnode"
	done

	return 0
}

# get_device_opts() - determine and set options for a crypttab target device
#
# expected arguments:
# * crypttab target device name (without /dev/mapper/ prefix)
# * optional extra options
#
# This function determines options for a crypttab target device and sets them
# accordingly. In order to detect the options, it parses the corresponding
# /etc/crypttab entry and takes optional extra options as second argument.
# Some sanity checks are done on the corresponding source device and configured
# options.
# After everything is processed, the options are saved in '$OPTIONS' for later
# access by parent functions.
#
get_device_opts() {
	local target source link extraopts rootopts opt key
	target="$1"
	extraopts="$2"
	KEYSCRIPT=""
	KEYFILE="" # key file to copy to the initramfs image
	CRYPTHEADER=""
	OPTIONS=""

	if [ -z "$target" ]; then
		echo "cryptsetup: WARNING: get_device_opts - invalid arguments" >&2
		return 1
	fi

	opt="$( awk -vtarget="$target" '$1 == target {gsub(/[ \t]+/," "); print; exit}' /etc/crypttab )"
	source=$( printf '%s' "$opt" | cut -d " " -f2 )
	key=$( printf '%s' "$opt" | cut -d " " -f3 )
	rootopts=$( printf '%s' "$opt" | cut -d " " -f4- )

	if [ -z "$opt" ] || [ -z "$source" ] || [ -z "$key" ] || [ -z "$rootopts" ]; then
		echo "cryptsetup: WARNING: invalid line in /etc/crypttab for $target - $opt" >&2
		return 1
	fi

	# Sanity checks for $source
	if [ -h "$source" ]; then
		link=$(readlink -nqe "$source")
		if [ -z "$link" ]; then
			echo "cryptsetup: WARNING: $source is a dangling symlink" >&2
			return 1
		fi

		if [ "$link" != "${link#/dev/mapper/}" ]; then
			echo "cryptsetup: NOTE: using $link instead of $source for $target" >&2
			source="$link"
		fi
	fi

	if [ "UUID=${source#UUID=}" = "$source" -a ! \( -b "/dev/disk/by-uuid/${source#UUID=}" -o -b "/dev/disk/by-partuuid/${source#UUID=}" \) ] || [ "UUID=${source#UUID=}" != "$source" -a ! -b "$source" ]; then
		echo "cryptsetup: WARNING: Invalid source device $source" >&2
	fi

	# Sanity checks for $key
	if [ "$key" = "/dev/random" ] || [ "$key" = "/dev/urandom" ]; then
		echo "cryptsetup: WARNING: target $target has a random key, skipped" >&2
		return 1
	fi

	if [ -n "$extraopts" ]; then
		rootopts="$extraopts,$rootopts"
	fi

	# We have all the basic options, let's go trough them
	OPTIONS="target=$target,source=$source"
	local IFS_BCK="$IFS"
	local IFS=", "
	unset HASH_FOUND
	unset LUKS_FOUND
	for opt in $rootopts; do
		case $opt in
			cipher=*)
				OPTIONS="$OPTIONS,$opt"
				;;
			size=*)
				OPTIONS="$OPTIONS,$opt"
				;;
			hash=*)
				OPTIONS="$OPTIONS,$opt"
				HASH_FOUND=1
				;;
			tries=*)
				OPTIONS="$OPTIONS,$opt"
				;;
			discard)
				OPTIONS="$OPTIONS,$opt"
				;;
			luks)
				LUKS_FOUND=1
				;;
			header=*)
				opt="${opt#header=}"
				if [ ! -e "$opt" ]; then
					echo "cryptsetup: WARNING: target $target has an invalid header, skipped" >&2
					return 1
				fi
				CRYPTHEADER="$opt"
				OPTIONS="$OPTIONS,header=$CRYPTHEADER"
				;;
			tcrypt)
				OPTIONS="$OPTIONS,$opt"
				;;
			keyscript=*)
				opt="${opt#keyscript=}"
				if [ ! -x "/lib/cryptsetup/scripts/$opt" ] && [ ! -x "$opt" ]; then
					echo "cryptsetup: WARNING: target $target has an invalid keyscript, skipped" >&2
					return 1
				fi
				KEYSCRIPT="$opt"
				OPTIONS="$OPTIONS,keyscript=/lib/cryptsetup/scripts/$(basename "$opt")"
				;;
			keyslot=*)
				OPTIONS="$OPTIONS,$opt"
				;;
			veracrypt)
				OPTIONS="$OPTIONS,$opt"
				;;
			lvm=*)
				OPTIONS="$OPTIONS,$opt"
				;;
			rootdev)
				OPTIONS="$OPTIONS,$opt"
				;;
			resumedev)
				OPTIONS="$OPTIONS,$opt"
				;;
			*)
				# Presumably a non-supported option
				;;
		esac
	done
	IFS="$IFS_BCK"

	# Warn for missing hash option, unless we have a LUKS partition
	if [ -z "$HASH_FOUND" ] && [ -z "$LUKS_FOUND" ]; then
		echo "WARNING: Option hash missing in crypttab for target $target, assuming ripemd160." >&2
		echo "         If this is wrong, this initramfs image will not boot." >&2
		echo "         Please read /usr/share/doc/cryptsetup/README.initramfs.gz and add" >&2
		echo "         the correct hash option to your /etc/crypttab."  >&2
	fi

	# Warn that header only applies to a LUKS partition currently
	if [ -n "$CRYPTHEADER" ] && [ -z "$LUKS_FOUND" ]; then
		echo "WARNING: Option LUKS missing in crypttab for target $target." >&2
		echo "         Headers are only supported for LUKS devices." >&2
	fi

	# If keyscript is set, the "key" is just an argument to the script
	if [ "$key" != "none" ] && [ -z "$KEYSCRIPT" ]; then
		case "$key" in
			$KEYFILE_PATTERN)
				KEYFILE="$key"
				key="/cryptroot-keyfiles/${target}.key"
				;;
			*)
				key=$(readlink -e "$key")
				# test whether $target is a root device (or parent of the root device)
				if printf '%s' "$OPTIONS" | grep -Eq '^(.*,)?rootdev(,.*)?$'; then
					echo "cryptsetup: WARNING: root target $target uses a key file, skipped" >&2
					return 1
				# test whether a) key file is not on root fs
				#           or b) root fs is not encrypted
				elif [ "$(stat -c %m -- "$key" 2>/dev/null)" != / ] || ! node_or_pv_is_in_crypttab $rootdevs; then
					echo "cryptsetup: WARNING: $target's key file $key is not on an encrypted root FS, skipped" >&2
					return 1
				fi
				if printf '%s' "$OPTIONS" | grep -Eq '^(.*,)?resumedev(,.*)?$'; then
					# we'll be able to decrypt the device, but won't be able to use it for resuming
					echo "cryptsetup: WARNING: resume device $source uses a key file" >&2
				fi
				# prepend "/root" (to be substituted by the real root FS
				# mountpoint "$rootmnt" in the boot script) to the
				# absolute filename
				key="/root$key"
				;;
		esac
		OPTIONS="$OPTIONS,keyscript=cat"
	fi
	OPTIONS="$OPTIONS,key=$key"
}

# get_device_modules() - determine required crypto kernel modules for device
#
# expected arguments:
# * crypttab target device name (without /dev/mapper/ prefix)
#
# This function determines the required crypto kernel modules for cipher,
# block cipher and optionally ivhash of the target device and returns them.
#
get_device_modules() {
	local node value cipher blockcipher ivhash
	node="$1"

	# Check the ciphers used by the active root mapping
	value=$(dmsetup table "$node" | cut -d " " -f4)
	cipher=$(echo "$value" | cut -d ":" -f1 | cut -d "-" -f1)
	blockcipher=$(echo "$value" | cut -d ":" -f1 | cut -d "-" -f2)
	ivhash=$(echo "$value" | cut -d ":" -s -f2)

	if [ -n "$cipher" ]; then
		echo "$cipher"
	else
		return 1
	fi

	if [ -n "$blockcipher" ] && [ "$blockcipher" != "plain" ]; then
		echo "$blockcipher"
	fi

	if [ -n "$ivhash" ] && [ "$ivhash" != "plain" ]; then
		echo "$ivhash"
	fi
	return 0
}

# canonical_device() - determine the 
#
# expected arguments:
# * device (either full path or LABEL=<x> or UUID=<y>)
# * optional options to the function
#
# This function takes a device as argument and determines the corresponding
# canonical device name.
# If option '--no-simplify' is given as second argument, then the origin device
# path after unraveling LABEL= and UUID= format and following symlinks is
# returned.
# If no option is given, the device is further unraveled and depending on the
# device path, either the corresponding device-mapper path (as found in
# /dev/mapper/) or the the corresponding disk symlink (as found in
# /dev/disk/by-*/) is returned.
#
canonical_device() {
	local dev altdev original
	dev="$1"
	opt="$2"

	if [ "${dev#LABEL=}" != "$dev" ]; then
		altdev="${dev#LABEL=}"
		dev="/dev/disk/by-label/$(printf '%s' "$altdev" | sed 's,/,\\x2f,g')"
	elif [ "${dev#UUID=}" != "$dev" ]; then
		altdev="${dev#UUID=}"
		dev="/dev/disk/by-uuid/$altdev"
	fi

	original="$dev"
	if [ -h "$dev" ]; then
		dev=$(readlink -e "$dev")
	fi

	if [ "$opt" = "--no-simplify" ]; then
		printf '%s' "$dev"
		return 0
	fi

	if [ "x${dev%/dev/dm-*}" = "x" ]; then
		# try to detect corresponding symlink in /dev/mapper/
		for dmdev in /dev/mapper/*; do
			if [ "$(readlink -e "$dmdev")" = "$dev" ]; then
				dev="$dmdev"
			fi
		done
	fi

	altdev="${dev#/dev/mapper/}"
	if [ "$altdev" != "$dev" ]; then
		printf '%s' "$altdev"
		return 0
	elif [ "x${original%/dev/disk/by-*/*}" = "x" ]; then
		# support crypttab UUID/LABEL entries
		# this is a /dev/disk/by-*/ path so return just the 'basename'
		echo "${original##/dev/disk/by-*/}"
		return 0
	fi

	echo "cryptsetup: WARNING: failed to detect canonical device of $original" >&2
	return 1
}

# add_device() - Process a given device and add to /conf/conf.d/cryptroot
#
# expected arguments:
# * device name (either crypttab target device name without /dev/mapper/ prefix
#                    or LVM device-mapper name in format '<VG>:<LV>')
#
# This function takes a device name, does all required processing and adds the
# result with all device options to /conf/conf.d/cryptroot in the initramfs.
# Additionally, it returns required kernel modules.
#
add_device() {
	local node nodes lvmnodes opts lastopts i count
	nodes="$1"
	opts=""     # Applied to all nodes
	lastopts="" # Applied to last node

	if [ -z "$nodes" ]; then
		return 0
	fi

	# Flag root and resume devices
	if printf '%s' "$rootdevs" | tr ' ' '\n' | grep -Fxq "$nodes"; then
		opts="${opts:+$opts,}rootdev"
	fi
	if printf '%s' "$resumedevs" | tr ' ' '\n' | grep -Fxq "$nodes"; then
		opts="${opts:+$opts,}resumedev"
	fi

	# Check that it is a node under /dev/mapper/
	# nodes=$(canonical_device "$nodes") || return 0

	# Can we find this node in crypttab
	if ! node_is_in_crypttab "$nodes"; then
		# dm node but not in crypttab, is it a lvm device backed by dm-crypt nodes?
		lvmnodes=$(get_lvm_deps "$nodes") || return 1

		# not backed by any dm-crypt nodes; stop here
		if [ -z "$lvmnodes" ]; then
		    return 0
		fi

		# It is a lvm device!
		opts="${opts:+$opts,}lvm=$nodes"
		nodes="$lvmnodes"
	fi

	# Prepare to setup each node
	count=$(printf '%s' "$nodes" | wc -w)
	i=1
	for node in $nodes; do
		# Prepare the additional options
		if [ $i -eq $count ]; then
			if [ -n "$lastopts" ]; then
				opts="${opts:+$opts,}$lastopts"
			fi
		fi

		# Get crypttab root options
		if ! get_device_opts "$node" "$opts"; then
			continue
		fi
		printf '%s\n' "$OPTIONS" >>"$DESTDIR/conf/conf.d/cryptroot"

		# If we have a keyscript, make sure it is included
		if [ -n "$KEYSCRIPT" ]; then
			if [ ! -d "$DESTDIR/lib/cryptsetup/scripts" ]; then
				mkdir -p "$DESTDIR/lib/cryptsetup/scripts"
			fi

			if [ -e "/lib/cryptsetup/scripts/$KEYSCRIPT" ]; then
				copy_exec "/lib/cryptsetup/scripts/$KEYSCRIPT" /lib/cryptsetup/scripts >&2
			elif [ -e "$KEYSCRIPT" ]; then
				copy_exec "$KEYSCRIPT" /lib/cryptsetup/scripts >&2
			elif KSTYPE="$(type "$KEYSCRIPT" 2>&1)"; then
				if [ -x "${KSTYPE#"$KEYSCRIPT" is }" ]; then
					copy_exec "${KSTYPE#"$KEYSCRIPT" is }" /lib/cryptsetup/scripts >&2
				fi
			else
				echo "cryptsetup: WARNING: failed to find keyscript $KEYSCRIPT" >&2
				continue
			fi
		elif [ -n "$KEYFILE" ]; then
			case "$KEYFILE" in
				$KEYFILE_PATTERN)
					mkdir -pm0700 "$DESTDIR/cryptroot-keyfiles"
					cp --preserve=all "$KEYFILE" "$DESTDIR/cryptroot-keyfiles/${node}.key"
					;;
			esac
		fi

		# If we have a LUKS header, make sure it is included
		# TODO: make it configurable to include the LUKS header into initramfs
		# disabled for now due to security reasons
		if [ -n "$CRYPTHEADER" ]; then
			if [ ! -d "$DESTDIR/conf/conf.d/cryptheader" ]; then
				mkdir -p "$DESTDIR/conf/conf.d/cryptheader"
			fi

			#if [ -e "$CONFDIR/conf.d/cryptheader/$CRYPTHEADER" ]; then
			#	copy_exec "$CONFDIR/conf.d/cryptheader/$CRYPTHEADER" /conf/conf.d/cryptheader >&2
			#elif [ -e "$CRYPTHEADER" ]; then
			#	copy_exec "$CRYPTHEADER" /conf/conf.d/cryptheader >&2
			#else
			#	echo "cryptsetup: WARNING: failed to find LUKS header $CRYPTHEADER" >&2
			#	continue
			#fi
		fi
		

		# Calculate needed modules
		modules=$(get_device_modules $node | sort | uniq)
		if [ -z "$modules" ]; then
			echo "cryptsetup: WARNING: failed to determine cipher modules to load for $node" >&2
			continue
		fi
		echo dm_mod
		echo dm_crypt
		echo "$modules"
		# Load hardware aes module
		if cpu_has_aesni; then
			echo aesni
		fi
		i=$(( $i + 1 ))
	done

	return 0
}

# cpu_has_aesni() - Detect whether the host CPU has AES-NI support
#
# expected arguments:
# * none
#
# This functions returns true when the host CPU has AES-NI support.
#
cpu_has_aesni() {
	return $(grep -q "^flags\s*:\s*.*aes" /proc/cpuinfo)
}

# add_crypto_modules() - determine kernel module path and add to initramfs
#
# expected arguments:
# * kernel module name
#
# This function takes a kernel module name, determines the corresponding path
# and runs manual_add_modules() from initramfs hook functions to add the module
# to the initramfs.
#
add_crypto_modules() {
	local mod file altmod found genericfound
	mod="$1"
	found=""
	genericfound=""

	if [ -z "$mod" ]; then
		return 1
	fi

	# We have several potential sources of modules (in order of preference):
	#
	#   a) /lib/modules/$VERSION/kernel/arch/$ARCH/crypto/$mod-$specific.ko
	#   b) /lib/modules/$VERSION/kernel/crypto/$mod_generic.ko
	#   c) /lib/modules/$VERSION/kernel/crypto/$mod.ko
	#
	# and (currently ignored):
	#
	#   d) /lib/modules/$VERSION/kernel/drivers/crypto/$specific-$mod.ko

	for file in $(find "$MODULESDIR/kernel/arch/" -name "$mod-*.ko" 2>/dev/null); do
		altmod="${file##*/}"
		altmod="${altmod%.ko}"
		manual_add_modules "$altmod"
		found="yes"
	done

	for file in $(find "$MODULESDIR/kernel/crypto/" -name "${mod}_generic.ko" 2>/dev/null); do
		altmod="${file##*/}"
		altmod="${altmod%.ko}"
		manual_add_modules "$altmod"
		found="yes"
		genericfound="yes"
	done

	if [ -z "$genericfound" ]; then
		for file in $(find "$MODULESDIR/kernel/crypto/" -name "${mod}.ko" 2>/dev/null); do
			altmod="${file##*/}"
			altmod="${altmod%.ko}"
			manual_add_modules "$altmod"
			found="yes"
		done
	fi

	if [ -z "$found" ]; then
		return 1
	fi

	return 0
}

#
# Begin real processing
#

setup="no"
rootdevs=""
usrdevs=""
resumedevs=""

# XXX Backward compatibility: remove once Stretch has been promoted stable
for v in CRYPTSETUP KEYFILE_PATTERN; do
	if eval [ "\${$v+x}" ]; then
		echo "WARNING: Setting $v in /etc/initramfs-tools/initramfs.conf" \
		     "is deprecated and will stop working in the future." \
		     "Use /etc/cryptsetup-initramfs/conf-hook instead." >&2
	fi
done

# Load the hook's config
if [ -f "/etc/cryptsetup-initramfs/conf-hook" ]; then
	. /etc/cryptsetup-initramfs/conf-hook
fi

# Include cryptsetup modules, regardless of _this_ machine configuration
if [ -n "$CRYPTSETUP" ] && [ "$CRYPTSETUP" != "n" ]; then
	setup="yes"
fi

if [ "$KEYFILE_PATTERN" ]; then
	setup="yes"
	case "${UMASK:-$(umask)}" in
		0[0-7]77) ;;
		*) echo "WARNING: permissive UMASK (${UMASK:-$(umask)})." \
		        "Private key material inside the initrd might be left unprotected." >&2
		;;
	esac
fi

# Find the root and resume device(s)
if [ -r /etc/crypttab ]; then
	rootdevs=$(get_fs_devices /)
	if [ -z "$rootdevs" ]; then
		echo "cryptsetup: WARNING: could not determine root device from /etc/fstab" >&2
	fi
	usrdevs=$(get_fs_devices /usr)
	resumedevs=$(get_resume_devices)
	initramfsdevs=$(get_initramfs_devices)
fi

# Load the config opts and modules for each device
for dev in $rootdevs $usrdevs $resumedevs $initramfsdevs; do
	if ! modules=$(add_device "$dev"); then
		echo "cryptsetup: FAILURE: could not determine configuration for $dev" >&2
		continue
	fi

	if [ -n "$modules" ]; then
		setup="yes"
	fi

	if [ "$setup" = "no" ]; then
		continue
	fi

	if [ "$MODULES" = "most" ]; then
		archcrypto="$(find "$MODULESDIR/kernel/arch" -type d -name "crypto" 2>/dev/null)"
		if [ -n "$archcrypto" ]; then
			copy_modules_dir "${archcrypto##*${MODULESDIR}/}"
		fi
		copy_modules_dir "kernel/crypto"
	else
		for mod in $modules; do
			add_crypto_modules $mod
		done
	fi
done

# With large initramfs, we always add a basic subset of modules
if [ "$MODULES" != "dep" ] && [ "$setup" = "yes" ]; then
	for mod in aes cbc chainiv cryptomgr krng sha256 xts; do
		add_crypto_modules $mod
	done
fi

# See if we need to add the basic components
if [ "$setup" = "yes" ]; then
	for mod in dm_mod dm_crypt; do
		manual_add_modules $mod
	done

	copy_exec /sbin/cryptsetup
	copy_exec /sbin/dmsetup
	copy_exec /lib/cryptsetup/askpass

	# We need sed. Either via busybox or as standalone binary.
	if [ "$BUSYBOX" = "n" ] || [ ! -e ${BUSYBOXDIR}/busybox ]; then
		copy_exec /bin/sed
	fi
fi

exit 0
```
</spoiler>

<spoiler title="diff /usr/share/initramfs-tools/hooks/cryptroot cryptroot">
```
45a46,51
>                       elif [ "$type" = "zfs" ]; then
>                               zpool="$(echo "$device"|sed 's#^/dev/zvol/##;s#\([^/]*\).*#\1#')"
>                               for ss in $(zpool list -Pv "$zpool"); do
>                                       cdev=$(canonical_device "$ss" 2>/dev/null) || continue
>                                       devices="${devices:+$devices }$cdev"
>                               done || return 0
375c381
<       if [ "UUID=${source#UUID=}" = "$source" -a ! -b "/dev/disk/by-uuid/${source#UUID=}" ] || [ "UUID=${source#UUID=}" != "$source" -a ! -b "$source" ]; then
---
>       if [ "UUID=${source#UUID=}" = "$source" -a ! \( -b "/dev/disk/by-uuid/${source#UUID=}" -o -b "/dev/disk/by-partuuid/${source#UUID=}" \) ] || [ "UUID=${source#UUID=}" != "$source" -a ! -b "$source" ]; then
```
</spoiler>

<spoiler title="/etc/initramfs-tools/scripts/local-top">
```bash
#!/bin/sh

PREREQ="cryptroot-prepare"

#
# Standard initramfs preamble
#
prereqs()
{
	# Make sure that cryptroot is run last in local-top
	for req in $(dirname $0)/*; do
		script=${req##*/}
		if [ $script != cryptroot ]; then
			echo $script
		fi
	done
}

case $1 in
prereqs)
	prereqs
	exit 0
	;;
esac

# source for log_*_msg() functions, see LP: #272301
. /scripts/functions

#
# Helper functions
#
message()
{
	if [ -x /bin/plymouth ] && plymouth --ping; then
		plymouth message --text="$@"
	elif [ -p /dev/.initramfs/usplash_outfifo ] && [ -x /sbin/usplash_write ]; then
		usplash_write "TEXT-URGENT $@"
	else
		echo "$@" >&2
	fi
	return 0
}

udev_settle()
{
	# Wait for udev to be ready, see https://launchpad.net/bugs/85640
	if command -v udevadm >/dev/null 2>&1; then
		udevadm settle --timeout=30
	elif command -v udevsettle >/dev/null 2>&1; then
		udevsettle --timeout=30
	fi
	return 0
}

parse_options()
{
	local cryptopts
	cryptopts="$1"

	if [ -z "$cryptopts" ]; then
		return 1
	fi

	# Defaults
	cryptcipher=aes-cbc-essiv:sha256
	cryptsize=256
	crypthash=ripemd160
	crypttarget=cryptroot
	cryptsource=""
	cryptheader=""
	cryptlvm=""
	cryptkeyscript=""
	cryptkey="" # This is only used as an argument to an eventual keyscript
	cryptkeyslot=""
	crypttries=3
	crypttcrypt=""
	cryptveracrypt=""
	cryptrootdev=""
	cryptdiscard=""
	CRYPTTAB_OPTIONS=""

	local IFS=" ,"
	for x in $cryptopts; do
		case $x in
		hash=*)
			crypthash=${x#hash=}
			;;
		size=*)
			cryptsize=${x#size=}
			;;
		cipher=*)
			cryptcipher=${x#cipher=}
			;;
		target=*)
			crypttarget=${x#target=}
			export CRYPTTAB_NAME="$crypttarget"
			;;
		source=*)
			cryptsource=${x#source=}
			if [ ${cryptsource#UUID=} != $cryptsource ]; then
				cryptsource="/dev/disk/by-uuid/${cryptsource#UUID=}"
			elif [ ${cryptsource#LABEL=} != $cryptsource ]; then
				cryptsource="/dev/disk/by-label/$(printf '%s' "${cryptsource#LABEL=}" | sed 's,/,\\x2f,g')"
			elif [ ${cryptsource#ID=} != $cryptsource ]; then
				cryptsource="/dev/disk/by-id/${cryptsource#ID=}"
			fi
			export CRYPTTAB_SOURCE="$cryptsource"
			;;
		header=*)
			cryptheader=${x#header=}
			if [ ! -e "$cryptheader" ] && [ -e "/conf/conf.d/cryptheader/$cryptheader" ]; then
				cryptheader="/conf/conf.d/cryptheader/$cryptheader"
			fi
			export CRYPTTAB_HEADER="$cryptheader"
			;;
		lvm=*)
			cryptlvm=${x#lvm=}
			;;
		keyscript=*)
			cryptkeyscript=${x#keyscript=}
			;;
		key=*)
			if [ "${x#key=}" != "none" ]; then
				cryptkey=${x#key=}
			fi
			export CRYPTTAB_KEY="$cryptkey"
			;;
		keyslot=*)
			cryptkeyslot=${x#keyslot=}
			;;
		tries=*)
			crypttries="${x#tries=}"
			case "$crypttries" in
			  *[![:digit:].]*)
				crypttries=3
				;;
			esac
			;;
		tcrypt)
			crypttcrypt="yes"
			;;
		veracrypt)
			cryptveracrypt="--veracrypt"
			;;
		rootdev)
			cryptrootdev="yes"
			;;
		discard)
			cryptdiscard="yes"
			;;
		esac
		PARAM="${x%=*}"
		if [ "$PARAM" = "$x" ]; then
			VALUE="yes"
		else
			VALUE="${x#*=}"
		fi
		CRYPTTAB_OPTIONS="$CRYPTTAB_OPTIONS $PARAM"
		eval export CRYPTTAB_OPTION_$PARAM="\"$VALUE\""
	done
	export CRYPTTAB_OPTIONS

	if [ -z "$cryptsource" ]; then
		message "cryptsetup ($crypttarget): source parameter missing"
		return 1
	fi
	return 0
}

activate_vg()
{
	# Sanity checks
	if [ ! -x /sbin/lvm ]; then
		message "cryptsetup ($crypttarget): lvm is not available"
		return 1
	fi

	# Detect and activate available volume groups
	/sbin/lvm vgscan
	/sbin/lvm vgchange -a y --sysinit
	return $?
}

setup_mapping()
{
	local opts count cryptopen cryptremove NEWROOT is_luks
	opts="$1"
	is_luks=0

	if [ -z "$opts" ]; then
		return 0
	fi

	parse_options "$opts" || return 1

	if [ -z "$cryptkeyscript" ]; then
		if [ ${cryptsource#/dev/disk/by-uuid/} != $cryptsource ]; then
			# UUIDs are not very helpful
			diskname="$crypttarget"
		else
			diskname="$cryptsource ($crypttarget)"
		fi
		cryptkeyscript="/lib/cryptsetup/askpass"
		cryptkey="1Please unlock disk $diskname: "
	elif ! type "$cryptkeyscript" >/dev/null; then
		message "cryptsetup ($crypttarget): error - script \"$cryptkeyscript\" missing"
		return 1
	fi

	if [ "$cryptkeyscript" = "cat" ] && [ "${cryptkey#/root/}" != "$cryptkey" ]; then
		# skip the mapping if the root FS is not mounted yet
		sed -rn 's/^\s*[^#]\S*\s+(\S+)\s.*/\1/p' /proc/mounts | grep -Fxq "$rootmnt" || return 1
		# substitute the "/root" prefix by the real root FS mountpoint otherwise
		cryptkey="${rootmnt}/${cryptkey#/root/}"
	fi

	if [ -n "$cryptheader" ] && ! type "$cryptheader" >/dev/null; then
		message "cryptsetup ($crypttarget): error - LUKS header \"$cryptheader\" missing"
		return 1
	fi

	# The same target can be specified multiple times
	# e.g. root and resume lvs-on-lvm-on-crypto
	if [ -e "/dev/mapper/$crypttarget" ]; then
		return 0
	fi

	modprobe -q dm_crypt

	# Make sure the cryptsource device is available
	if [ ! -e $cryptsource ]; then
		activate_vg
	fi

	# If the encrypted source device hasn't shown up yet, give it a
	# little while to deal with removable devices

	# the following lines below have been taken from
	# /usr/share/initramfs-tools/scripts/local, as suggested per
	# https://launchpad.net/bugs/164044
	if [ ! -e "$cryptsource" ]; then
		log_begin_msg "Waiting for encrypted source device..."

		# Default delay is 180s
		if [ -z "${ROOTDELAY}" ]; then
			slumber=180
		else
			slumber=${ROOTDELAY}
		fi
		if [ -x /sbin/usplash_write ]; then
			/sbin/usplash_write "TIMEOUT ${slumber}" || true
		fi

		slumber=$(( ${slumber} * 10 ))
		while [ ! -e "$cryptsource" ]; do
			# retry for LVM devices every 10 seconds
			if [ ${slumber} -eq $(( ${slumber}/100*100 )) ]; then
				activate_vg
			fi

			/bin/sleep 0.1
			slumber=$(( ${slumber} - 1 ))
			[ ${slumber} -gt 0 ] || break
		done

		if [ ${slumber} -gt 0 ]; then
			log_end_msg 0
		else
			log_end_msg 1 || true
		fi
		if [ -x /sbin/usplash_write ]; then
			/sbin/usplash_write "TIMEOUT 15" || true
		fi
 	fi
	udev_settle

	# We've given up, but we'll let the user fix matters if they can
	if [ ! -e "${cryptsource}" ]; then
		
		echo "  ALERT! ${cryptsource} does not exist."
		echo "	Check cryptopts=source= bootarg: cat /proc/cmdline"
		echo "	or missing modules, devices: cat /proc/modules; ls /dev"
		panic -r "Dropping to a shell. Will skip ${cryptsource} if you can't fix."
	fi

	if [ ! -e "${cryptsource}" ]; then
		return 1
	fi


	# Prepare commands
	cryptopen="/sbin/cryptsetup -T 1"
	if [ "$cryptdiscard" = "yes" ]; then
		cryptopen="$cryptopen --allow-discards"
	fi
	if [ -n "$cryptheader" ]; then
		cryptopen="$cryptopen --header=$cryptheader"
	fi
	if [ -n "$cryptkeyslot" ]; then
		cryptopen="$cryptopen --key-slot=$cryptkeyslot"
	fi
	if /sbin/cryptsetup isLuks ${cryptheader:-$cryptsource} >/dev/null 2>&1; then
		is_luks=1
		cryptopen="$cryptopen open --type luks $cryptsource $crypttarget --key-file=-"
	elif [ "$crypttcrypt" = "yes" ]; then
		cryptopen="$cryptopen open --type tcrypt $cryptveracrypt $cryptsource $crypttarget"
	else
		cryptopen="$cryptopen -c $cryptcipher -s $cryptsize -h $crypthash open --type plain $cryptsource $crypttarget --key-file=-"
	fi
	cryptremove="/sbin/cryptsetup remove $crypttarget"
	NEWROOT="/dev/mapper/$crypttarget"

	# Try to get a satisfactory password $crypttries times
	count=0
	while [ $crypttries -le 0 ] || [ $count -lt $crypttries ]; do
		export CRYPTTAB_TRIED="$count"
		if [ $count -gt 1 ]; then
			/bin/sleep 3
		fi

		if [ -z "$cryptkeyscript" -a "$is_luks" -eq "1" ]; then
			cryptkey="Unlocking the disk $cryptsource ($crypttarget)\nEnter passphrase: "
			if [ -x /bin/plymouth ] && plymouth --ping; then
				cryptkeyscript="plymouth ask-for-password --prompt"
				cryptkey=$(echo -e "$cryptkey")
			else
				cryptkeyscript="/lib/cryptsetup/askpass"
			fi
		fi

		if [ -n "$CACHED_PASSWORD" ]; then
			if ! crypttarget="$crypttarget" cryptsource="$cryptsource" \
			     echo -n "$CACHED_PASSWORD" | $cryptopen 2>/dev/null; then
				unset CACHED_PASSWORD
			fi
		fi

		count=$(( $count + 1 ))

		if [ -z "$CACHED_PASSWORD" ]; then
			CACHED_PASSWORD="`$cryptkeyscript \"$cryptkey\"`"
			if ! crypttarget="$crypttarget" cryptsource="$cryptsource" \
			     echo -n "$CACHED_PASSWORD" | $cryptopen; then
				message "cryptsetup: cryptsetup failed, bad password or options?"
				unset CACHED_PASSWORD
				continue
			fi
		fi

		if [ ! -e "$NEWROOT" ]; then
			message "cryptsetup ($crypttarget): unknown error setting up device mapping"
			return 1
		fi

		#FSTYPE=''
		#eval $(fstype < "$NEWROOT")
		FSTYPE="$(/sbin/blkid -s TYPE -o value "$NEWROOT")"

		# See if we need to setup lvm on the crypto device
		#if [ "$FSTYPE" = "lvm" ] || [ "$FSTYPE" = "lvm2" ]; then
		if [ "$FSTYPE" = "LVM_member" ] || [ "$FSTYPE" = "LVM2_member" ]; then
			if [ -z "$cryptlvm" ]; then
				message "cryptsetup ($crypttarget): lvm fs found but no lvm configured"
				return 1
			elif ! activate_vg; then
				# disable error message, LP: #151532
				#message "cryptsetup ($crypttarget): failed to setup lvm device"
				return 1
			fi

			# Apparently ROOT is already set in /conf/param.conf for
			# flashed kernels at least. See bugreport #759720.
			if [ -f /conf/param.conf ] && grep -q "^ROOT=" /conf/param.conf; then
				NEWROOT=$(sed -n 's/^ROOT=//p' /conf/param.conf)
			else
				NEWROOT=${cmdline_root:-/dev/mapper/$cryptlvm}
				if [ "$cryptrootdev" = "yes" ]; then
					# required for lilo to find the root device
					echo "ROOT=$NEWROOT" >>/conf/param.conf
				fi
			fi
			#eval $(fstype < "$NEWROOT")
			FSTYPE="$(/sbin/blkid -s TYPE -o value "$NEWROOT")"
		fi

		#if [ -z "$FSTYPE" ] || [ "$FSTYPE" = "unknown" ]; then
		if [ -z "$FSTYPE" ]; then
			message "cryptsetup ($crypttarget): unknown fstype, bad password or options?"
			udev_settle
			$cryptremove
			unset CACHED_PASSWORD
			continue
		fi

		# decrease $count by 1, apparently last try was successful.
		count=$(( $count - 1 ))

		message "cryptsetup ($crypttarget): set up successfully"
		
		export CACHED_PASSWORD
		
		break
	done

	failsleep=60 # make configurable later?

	if [ "$cryptrootdev" = "yes" ] && [ $crypttries -gt 0 ] && [ $count -ge $crypttries ]; then
		message "cryptsetup ($crypttarget): maximum number of tries exceeded"
		message "cryptsetup: going to sleep for $failsleep seconds..."
		sleep $failsleep
		exit 1
	fi

	udev_settle
	return 0
}

exit_script()
{
	CACHED_PASSWORD="`dd bs=512 if=/dev/random count=1 2>/dev/null `"
	unset CACHED_PASSWORD
	exit $1
}

#
# Begin real processing
#

# Do we have any kernel boot arguments?
cmdline_cryptopts=''
unset cmdline_root
for opt in $(cat /proc/cmdline); do
	case $opt in
	cryptopts=*)
		opt="${opt#cryptopts=}"
		if [ -n "$opt" ]; then
			if [ -n "$cmdline_cryptopts" ]; then
				cmdline_cryptopts="$cmdline_cryptopts $opt"
			else
				cmdline_cryptopts="$opt"
			fi
		fi
		;;
	root=*)
		opt="${opt#root=}"
		case $opt in
		/*) # Absolute path given. Not lilo major/minor number.
			cmdline_root=$opt
			;;
		*) # lilo major/minor number (See #398957). Ignore
		esac
		;;
	esac
done

if [ -n "$cmdline_cryptopts" ]; then
	# Call setup_mapping separately for each possible cryptopts= setting
	for cryptopt in $cmdline_cryptopts; do
		setup_mapping "$cryptopt"
	done
	exit 0
fi

# Do we have any settings from the /conf/conf.d/cryptroot file?
if [ -r /conf/conf.d/cryptroot ]; then
	while read mapping <&3; do
		setup_mapping "$mapping" 3<&-
	done 3< /conf/conf.d/cryptroot
fi

exit_script 0
```
</spoiler>
<spoiler title="diff /usr/share/initramfs-tools/scripts/local-top/cryptroot cryptroot
">
```

35a36,37
> 	elif [ -p /dev/.initramfs/usplash_outfifo ] && [ -x /sbin/usplash_write ]; then
> 		usplash_write "TEXT-URGENT $@"
101a104,105
> 			elif [ ${cryptsource#ID=} != $cryptsource ]; then
> 				cryptsource="/dev/disk/by-id/${cryptsource#ID=}"
182c186
< 	local opts count cryptopen cryptremove NEWROOT
---
> 	local opts count cryptopen cryptremove NEWROOT is_luks
183a188
> 	is_luks=0
199c204
< 		cryptkey="Please unlock disk $diskname: "
---
> 		cryptkey="1Please unlock disk $diskname: "
244a250,252
> 		if [ -x /sbin/usplash_write ]; then
> 			/sbin/usplash_write "TIMEOUT ${slumber}" || true
> 		fi
262a271,273
> 		if [ -x /sbin/usplash_write ]; then
> 			/sbin/usplash_write "TIMEOUT 15" || true
> 		fi
291a303
> 		is_luks=1
304a317,337
> 		if [ $count -gt 1 ]; then
> 			/bin/sleep 3
> 		fi
> 
> 		if [ -z "$cryptkeyscript" -a "$is_luks" -eq "1" ]; then
> 			cryptkey="Unlocking the disk $cryptsource ($crypttarget)\nEnter passphrase: "
> 			if [ -x /bin/plymouth ] && plymouth --ping; then
> 				cryptkeyscript="plymouth ask-for-password --prompt"
> 				cryptkey=$(echo -e "$cryptkey")
> 			else
> 				cryptkeyscript="/lib/cryptsetup/askpass"
> 			fi
> 		fi
> 
> 		if [ -n "$CACHED_PASSWORD" ]; then
> 			if ! crypttarget="$crypttarget" cryptsource="$cryptsource" \
> 			     echo -n "$CACHED_PASSWORD" | $cryptopen 2>/dev/null; then
> 				unset CACHED_PASSWORD
> 			fi
> 		fi
> 
307c340,341
< 		if [ ! -e "$NEWROOT" ]; then
---
> 		if [ -z "$CACHED_PASSWORD" ]; then
> 			CACHED_PASSWORD="`$cryptkeyscript \"$cryptkey\"`"
309,310c343,345
< 			     $cryptkeyscript "$cryptkey" | $cryptopen; then
< 				message "cryptsetup ($crypttarget): cryptsetup failed, bad password or options?"
---
> 			     echo -n "$CACHED_PASSWORD" | $cryptopen; then
> 				message "cryptsetup: cryptsetup failed, bad password or options?"
> 				unset CACHED_PASSWORD
355a391
> 			unset CACHED_PASSWORD
362a399,401
> 		
> 		export CACHED_PASSWORD
> 		
378a418,424
> exit_script()
> {
> 	CACHED_PASSWORD="`dd bs=512 if=/dev/random count=1 2>/dev/null `"
> 	unset CACHED_PASSWORD
> 	exit $1
> }
> 
425c471
< exit 0
---
> exit_script 0
```
</spoiler>

Дополнить crypttab:

`echo "root_crypt1 /dev/disk/by-id/ata-Samsung_SSD_850_PRO-part3 none luks,discard" >> /mnt/etc/crypttab`
`echo "root_crypt2 /dev/disk/by-id/ata-Micron_1100-part3 none luks,discard" >> /mnt/etc/crypttab`

**Здесь диски указываются не по UUID, это сделано специально**.
Хук cryptroot, либо поправленный мною скрипт (о чём ниже) почему-то некорректно отработали с UUID-ами и не увидели разделы.


### Установить загрузчик и убедиться, что он распознаёт корневую ФС

`apt-get install grub-pc`
`grub-probe /` - должен вывести "zfs"

**Предпочтительный вариант установки загрузчика на зеркало ZFS, возможно посмотреть [в этой статье](https://habr.com/post/358914/)**


### Настроить загрузчик и установить в загрузочную запись

`echo GRUB_PRELOAD_MODULES=\"part_gpt zfs\" >> /etc/default/grub`
`echo GRUB_DISABLE_OS_PROBER=true >> /etc/default/grub`
`echo "export ZPOOL_VDEV_NAME_PATH=YES" > /etc/profile.d/grub2_zpool_fix.sh`
`ZPOOL_VDEV_NAME_PATH=YES update-grub`
`update-initramfs -u -k all`


### Проинициализировать загрузочные разделы

`cd && tar -C / -cf boot.tar /boot`
`mkfs.ext4 -L boot1 -m0 /dev/disk/by-id/ata-Samsung_SSD_850_PRO-part2`
`mkfs.ext4 -L boot2 -m0 /dev/disk/by-id/ata-Micron_1100-part2`


### Установить загрузчик

`mount /dev/disk/by-id/ata-Samsung_SSD_850_PRO-part2 /boot && tar -C / -xf boot.tar`
`update-initramfs -k all -u -t && update-grub`
`grub-install --bootloader-id=debian1 --recheck --no-floppy /dev/disk/by-id/ata-Samsung_SSD_850_PRO`
`umount /boot`
`mount /dev/disk/by-id/ata-Micron_1100-part2 /boot && tar -C / -xf boot.tar`
`update-initramfs -k all -u -t && update-grub`
`grub-install --bootloader-id=debian2 --recheck --no-floppy /dev/disk/by-id/ata-Micron_1100`
`umount /boot`


### Установить пароль root

`passwd`


### Создать снимок

`zfs snapshot rpool/ROOT/debian@install`


### Выполнить отмонтирование и перезагрузку

`umount /tmp`
`exit`
`mount | grep -v zfs | tac | awk '/\/mnt/ {print $3}' | xargs -i{} umount -lf {}`
`zpool export rpool`
`reboot`


### Загрузиться в установленную систему и выполнить её донастройку

Проверить работоспособность пула (пул и оба диска в нём должны быть ONLINE):
`zpool status -v`

Установить SSH сервер.
Создать нового пользователя:
`zfs create rpool/home/user`
`adduser user`
`cp -a /etc/skel/.[!.]* /home/user`
`chown -R user:user /home/user`
`usermod -a -G audio,cdrom,dip,floppy,netdev,plugdev,sudo,video user`


### Обновить систему

`apt dist-upgrade --yes`

**После этого шага у вас есть Debian с корнем на шифрованном зеркале ZFS**.


## Предполагаемые FAQ

### Не снизит ли шифрование производительность?

Снизит.
Но это не имеет большого значение по следующим причинам:
- В большинстве новых CPU (в особенности серверных) поддерживается AES-NI.
- Это диск с ОС, от которого не требуется сверх-быстродействия.
- Всегда возможно использовать кэширование (preload, например).

В целом, снижение быстродействия не то что, невозможно будет заметить, а даже сложно будет измерить.


### Почему используется не EFI загрузчик?

На это есть две причины:
- Плата, которую я использую, плохо загружается с EFI. 
- Обычный /boot c grub внутри легко потом включить в зеркало ZFS, что не так просто сделать с EFI разделами.


### Почему не используется ZFS шифрование?

Потому что, на данный момент оно ещё сырое и оно шифрует не всё, оставляя метаданные.


### Почему /boot не на ZFS?

Потому что, пока я этого ещё не сделал. Но grub поддерживает это.


### Почему загрузка идёт не с шифрованного раздела?

Grub поддерживает эту возможность, но пароль придётся вводить трижды (сначала, на каждый корневой раздел, затем для cryptroot).
И есть у этого способа ещё недостатки, о которых я не буду здесь говорить.


### Почему не используется FreeBSD, ведь там же даже шифрование с корнем на ZFS "из коробки"?

Потому что, я хочу сделать NAS с WEB-интерфейсом. FreeBSD - это ОС, которую придётся допиливать, чтобы работало приложение FreeNAS.
OpenMediaVault - это пакет, который я могу поставить в Debian.


## Благодарности

Хочу выразить свою благодарность, прежде всего, русскому сообществу Debian: они сильно помогли, отвечая на мои вопросы.
Сообществу FreeNAS, которое имеет огромную базу знаний по ZFS.
Людям, которые портировали ZFS на Linux.
