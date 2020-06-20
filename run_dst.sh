#!/bin/bash

# Read in variables from YAML file
while IFS= read -r line; do
	if [ "$line" == "---" ]; then
		continue
	fi
	strarr=($(echo $line | tr ":" "\n"))
	declare "${strarr[0]}"="${strarr[1]}"
done < vars.yml

function fail()
{
        echo Error: "$@" >&2
        exit 1
}

function check_for_file()
{
    if [ ! -e "$1" ]; then
            fail "Missing file: $1"
    fi
}

cd "$steamcmd_dir" || fail "Missing $steamcmd_dir directory!"

check_for_file "steamcmd.sh"
check_for_file "$game_dir/$cluster_name/cluster.ini"
check_for_file "$game_dir/$cluster_name/cluster_token.txt"
check_for_file "$game_dir/$cluster_name/Master/server.ini"
check_for_file "$game_dir/$cluster_name/Caves/server.ini"

if [ "$check_update" -eq 1 ]; then
    "$steamcmd_dir/steamcmd.sh" +login $login +force_install_dir "$install_dir" +app_update 343050 validate +quit
fi

check_for_file "$install_dir/mods/server_mods.txt"

cp "$install_dir/mods/server_mods.txt" "$install_dir/mods/dedicated_server_mods_setup.lua"

check_for_file "$install_dir/bin"

cd "$install_dir/bin" || fail 

if [ ! -e "$dst_pipe" ]; then
    mkfifo "$dst_pipe"
fi

run_shard=(./dontstarve_dedicated_server_nullrenderer)
run_shard+=(-cluster "$cluster_name")
run_shard+=(-monitor_parent_process $$)

"${run_shard[@]}" -shard Caves | sed 's/^/Caves:  /' &
while true
do
    "${run_shard[@]}" -shard Master | sed 's/^/Master: /'
    break
done <> "$dst_pipe"
