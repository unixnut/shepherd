REGION=ap-southeast-2
hosts.txt: ~/.ssh/config
	awk 'function maybe_print_var(var, val) { if (val != "") printf " ansible_" var "=" val; }  \
	     function flush_host()  {  \
	                              if (instance_id != "")  \
	                                {  \
	                                  printf("%s cloud_provider=aws cloud_region=$(REGION) cloud_instance_id=%s", name, instance_id);  \
	                                  maybe_print_var("ssh_host", ssh_host);  \
	                                  maybe_print_var("ssh_port", ssh_port);  \
	                                  maybe_print_var("ssh_user", ssh_user);  \
	                                  maybe_print_var("ssh_private_key_file", ssh_private_key_file);  \
	                                  print "";  \
	                                }  \
	                            }  \
	     /^[ \t]*# i-[0-9a-f]*/ { flush_host(); instance_id = substr($$0, 3, 10); start_line=NR }  \
	     $$1 == "Host"          {  \
	                              # Process a Host entry, but only for real  \
	                              # if on the line after the # i-XXXXXXX  \
	                              if (NR == start_line+1)  \
	                                name = $$2;  \
	                              else  \
	                                {  \
	                                  flush_host();  \
	                                  instance_id="";  \
	                                }  \
	                              # scrub everything else  \
	                              ssh_host="";  \
	                              ssh_port="";  \
	                              ssh_user="";  \
	                              ssh_private_key_file="";  \
	                              }  \
	     $$1 == "HostName"        { ssh_host = $$2; };  \
	     $$1 == "Port"            { ssh_port = $$2; };  \
	     $$1 == "User"            { ssh_user = $$2; };  \
	     $$1 == "IdentityFile"    { match($$0, /IdentityFile[ \t]*/); ssh_private_key_file = substr($$0, RSTART + RLENGTH); };  \
	     END                      { flush_host(); }'  \
	  $^ > $@
