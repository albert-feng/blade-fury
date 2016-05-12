#!/bin/sh
#
# ssh-import-id - Authorize SSH public keys from trusted online identities.
#
# Copyright (c) 2016 Dustin Kirkland <dustin.kirkland@gmail.com>
#
# ssh-import-id is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# ssh-import-id is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ssh-import-id.  If not, see <http://www.gnu.org/licenses/>.

set -e

for i in $@; do
	ssh-import-id gh:$i
done
