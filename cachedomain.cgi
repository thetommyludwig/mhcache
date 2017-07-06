#!/usr/local/cpanel/3rdparty/bin/perl
###############################################################################
# MH Cache
# URL: http://
# Author: Tom Ludwig
###############################################################################
use strict;
use DBI;
use CGI;
use CGI qw(:standard);
use CGI::Carp qw(warningsToBrowser fatalsToBrowser);


print "Content-type:text/html\r\n\r\n";

my @leclear = param('leclear');
foreach my $leclear (@leclear) {
    print "Clearing cache for domain $leclear.<br>";
    my $owner = `awk -F ': ' '/^$leclear/{print \$2}' /etc/userdomains`;
    chomp($owner);
    my $directory = "/home/$owner/mhcache";
    print "$directory\n";
    if(-e $directory) {
        system( "rm -fr $directory/*" );
    }
    else {
        print "Unable to clear cache."
    }
}

my @domains = param('ledomain');
foreach my $domain (@domains) {
    print "Enabling cache for domain $domain.\n";
    my $owner = `awk -F ': ' '/$domain/{print \$2}' /etc/userdomains`;
    chomp($owner);
    my $group = "nobody";

    my $uid = getpwnam $owner;
    my $gid = getgrnam $group;
    
    my $directory = "/etc/apache2/conf.d/userdata/std/2/$owner/$domain";
       
    unless(-e $directory or mkdir $directory) {
        print "Unable to create $directory\n";
    }
    system( "touch $directory/mhcache.conf" );

    my $cacheroot = "/tmp/mhcache/$owner";
    # Create and set cache directory
    unless(-e "/tmp/mhcache" or mkdir "/tmp/mhcache") {
        print "Unable to create /tmp/mhcache\n";
    }

    unless(-e $cacheroot or mkdir $cacheroot) {
        print "Unable to create $cacheroot\n";
    }

    chown $uid, $gid, "/tmp/mhcache/$owner";
    chmod 0770, "/tmp/mhcache/$owner";

    system( "cat /usr/local/cpanel/whostmgr/docroot/cgi/managedhostcache/vhostinclude.conf > $directory/mhcache.conf" );

    my $outfile = "$directory/mhcache.conf";
    open (FILE, ">> $outfile") || die "problem opening $outfile\n";
    print FILE "CacheRoot '/tmp/mhcache/$owner'";
    close(FILE);

    system( "/scripts/rebuildhttpdconf && /scripts/restartsrv_apache >> /dev/null" );
}

1;
