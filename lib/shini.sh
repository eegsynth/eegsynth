# shini - portable INI library for sh (with extras for bash)
#
# This code is released freely under the MIT license - see the shipped LICENSE document.
# For the latest version etc, please see https://github.com/wallyhall/shini
#

shini_function_exists()
{
	type "$1" > /dev/null 2>&1
	return $?
}

# @param inifile Filename of INI file to parse
# @param postfix Function postfix for callbacks (optional)
# @param extra Extra argument for callbacks (optional)
shini_parse()
{

	RX_KEY='[a-zA-Z0-9_\-]'
	RX_VALUE="[^;\"]"
	RX_SECTION='[a-zA-Z0-9_\-]'
	RX_WS='[ 	]'
	RX_QUOTE='"'
	RX_HEX='[0-9A-F]'
	POSTFIX=''
	EXTRA1=''
	EXTRA2=''
	EXTRA3=''
	
	if [ $# -ge 2 ] && [ ! -z "$2" ]; then
	    POSTFIX="_$2"
	fi
	
	if [ $# -ge 3 ] && ! [ -z "$3" ]; then
	    EXTRA1="$3"
	fi
	
	if [ $# -ge 4 ] && [ ! -z "$4" ]; then
	    EXTRA2="$4"
	fi
	
	if [ $# -ge 5 ] && [ ! -z "$5" ]; then
	    EXTRA3="$5"
	fi
	
	if ! shini_function_exists "__shini_parsed${POSTFIX}"; then
		printf 'shini: __shini_parsed%s function not declared.\n' "${POSTFIX}" 1>&2
		exit 255
	fi

	if [ $# -lt 1 ]; then
		if shini_function_exists "__shini_no_file_passed{$POSTFIX}"; then
			"__shini_no_file_passed${POSTFIX}" "$EXTRA1" "$EXTRA2" "$EXTRA3"
		else
			printf 'shini: Argument 1 needs to specify the INI file to parse.\n' 1>&2
			exit 254
		fi
	fi
	INI_FILE="$1"

	if [ ! -r "$INI_FILE" ]; then
		if shini_function_exists "__shini_file_unreadable${POSTFIX}"; then
			"__shini_file_unreadable${POSTFIX}" "$INI_FILE" "$EXTRA1" "$EXTRA2" "$EXTRA3"
		else
			printf 'shini: Unable to read INI file:\n  `%s`\n' "$INI_FILE" 1>&2
			exit 253
		fi
	fi

	# Iterate INI file line by line
	LINE_NUM=0
	SECTION=''
	while read LINE || [ -n "$LINE" ]; do  # -n $LINE catches final line if not empty
		# Check for new sections
		if printf '%s' "$LINE" | \
		  grep -qe "^${RX_WS}*\[${RX_SECTION}${RX_SECTION}*\]${RX_WS}*$"; then
			SECTION="$(printf '%s' "$LINE" | \
				sed "s/^${RX_WS}*\[\(${RX_SECTION}${RX_SECTION}*\)\]${RX_WS}*$/\1/")"
				
            if shini_function_exists "__shini_parsed_section${POSTFIX}"; then
				"__shini_parsed_section${POSTFIX}" "$SECTION" "$EXTRA1" "$EXTRA2" "$EXTRA3"
			fi
			
			continue
		fi
		
		# Check for new values
		if printf '%s' "$LINE" | \
		  grep -qe "^${RX_WS}*${RX_KEY}${RX_KEY}*${RX_WS}*="; then
			KEY="$(printf '%s' "$LINE" | \
				sed "s/^${RX_WS}*\(${RX_KEY}${RX_KEY}*\)${RX_WS}*=.*$/\1/")"
			VALUE="$(printf '%s' "$LINE" | \
				sed "s/^${RX_WS}*${RX_KEY}${RX_KEY}*${RX_WS}*=${RX_WS}*${RX_QUOTE}\{0,1\}\(${RX_VALUE}*\)${RX_QUOTE}\{0,1\}\(${RX_WS}*\;.*\)*$/\1/")"
			
			if printf '%s' "$VALUE" | grep -qe "^0x${RX_HEX}${RX_HEX}*$"; then
				VALUE=$(printf '%d' "$VALUE")
			fi
			
			"__shini_parsed${POSTFIX}" "$SECTION" "$KEY" "$VALUE" "$EXTRA1" "$EXTRA2" "$EXTRA3"
						
			if shini_function_exists "__shini_parsed_comment${POSTFIX}"; then
			    if printf '%s' "$LINE" | grep -q ";"; then
        			COMMENT="$(printf '%s' "$LINE" | \
    	    			sed "s/^.*\;\(.*\)$/\1/")"
        			 "__shini_parsed_comment${POSTFIX}" "$COMMENT" "$EXTRA1" "$EXTRA2" "$EXTRA3"
    	        fi
            fi
            
			continue
		fi
		
		# Announce parse errors
		if [ "$LINE" != '' ] &&
		  ! printf '%s' "$LINE" | grep -qe "^${RX_WS}*;.*$" &&
		  ! printf '%s' "$LINE" | grep -qe "^${RX_WS}*$"; then
			if shini_function_exists "__shini_parse_error${POSTFIX}"; then
				"__shini_parse_error${POSTFIX}" $LINE_NUM "$LINE" "$EXTRA1" "$EXTRA2" "$EXTRA3"
			else
				printf 'shini: Unable to parse line %d:\n  `%s`\n' $LINE_NUM "$LINE"
			fi
		fi
		
		LINE_NUM=$((LINE_NUM+1))
	done < "$INI_FILE"

}

# @param inifile Filename of INI file to write to
# @param section Section of INI file to write to
# @param variable Variable name to add/update/delete
# @param value Value to add/update, do not specify to delete
shini_write()
{
    # This is not yet optimised (early write support only) - 
    # We actually re-parse the entire file, looking for the location in which to
    # write the new value, writing out everything we parse as-is meanwhile.

    # Declare the following if you want particular behaviour (like skipping
    # broken INI file content or handling an unreadable file etc).
    #  __shini_no_file_passed__writer()
    #  __shini_file_unreadable__writer()
    #  __shini_parse_error__writer()
    
    # Writer callbacks, used for writing the INI file content
    __shini_parsed_section__writer()
    {
        # Validate the last section wasn't the target section
        if [ "$LAST_SECTION" = "$WRITE_SECTION" ]; then
            # If it was, and the value wasn't written already, write it
            if [ $VALUE_WRITTEN -eq 0 ]; then
                printf "\n%s=%s" "$WRITE_KEY" "$WRITE_VALUE" >> "$INI_FILE_TEMP"
                VALUE_WRITTEN=1
            fi
        fi
        printf "\n[%s]" "$1" >> "$INI_FILE_TEMP"
        
        LAST_SECTION="$1"
    }
    
    __shini_parsed_comment__writer()
    {
        printf ";%s" "$1" >> "$INI_FILE_TEMP"
    }
    
    __shini_parsed__writer()
    {
        if [ "$1" = "$WRITE_SECTION" ]; then
            if [ "$2" = "$WRITE_KEY" ]; then
                if [ ! -z "$WRITE_VALUE" ]; then
                    printf "\n%s=%s" "$WRITE_KEY" "$WRITE_VALUE" >> "$INI_FILE_TEMP"
                fi
                VALUE_WRITTEN=1
                return
            fi
        fi
        
        printf "\n%s=%s" "$2" "$3" >> "$INI_FILE_TEMP"
    }
    
    if [ $# -lt 3 ]; then
        if shini_function_exists "__shini_no_file_passed"; then
            __shini_no_file_passed
        else
            printf 'shini: Argument 1 needs to specify the INI file to write.\n' 1>&2
            exit 254
        fi
    fi
    
    INI_FILE="$1"
    INI_FILE_TEMP="$(mktemp -t shini_XXXXXX)"       
    
    WRITE_SECTION="$2"
    WRITE_KEY="$3"
    WRITE_VALUE="$4"
    LAST_SECTION=""
    VALUE_WRITTEN=0
    
    shini_parse "$1" "_writer" "$2" "$3" "$4"
    # Still not written out yet
    if [ $VALUE_WRITTEN -eq 0 ]; then
        # Check if final existing section was target one, add it if not
        if [ "$LAST_SECTION" != "$WRITE_SECTION" ]; then
            printf "\n[%s]" "$WRITE_SECTION" >> "$INI_FILE_TEMP"
        fi
        # Write value at end of file
        printf "\n%s=%s" "$WRITE_KEY" "$WRITE_VALUE" >> "$INI_FILE_TEMP"
    fi
    
    mv "$INI_FILE_TEMP" "$INI_FILE"
}
