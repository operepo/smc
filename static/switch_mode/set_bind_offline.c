#include <stdio.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

int main()
{

// Copy configs
system("/bin/cp -f /etc/bind/named.conf.offline /etc/bind/named.conf");

// Restart bind service
int ret = setuid(0);
char *args[] = {"bind9", "restart"}; 
execv("/etc/init.d/bind9", args);

return 0;
}
