#!/usr/local/cpanel/3rdparty/bin/perl
###############################################################################
# MH Cache 
# URL: http://
# Author: Tom Ludwig
###############################################################################
## no critic (RequireUseWarnings, ProhibitExplicitReturnUndef, ProhibitMixedBooleanOperators, RequireBriefOpen)
use strict;
use File::Find;
use Fcntl qw(:DEFAULT :flock);
use Sys::Hostname qw(hostname);
use IPC::Open3;
use Cpanel::Form            ();
use Whostmgr::HTMLInterface ();
use Whostmgr::ACLS          ();
use Cpanel::Encoder::Tiny   ();
use Cpanel::FindBin         ();
use Cpanel::Locale          ('lh');
use Cpanel::SafeRun::Errors ();
use CGI::Carp qw(fatalsToBrowser);
use GD;

use lib '/usr/local/cpanel';
require Cpanel::Form;
require Cpanel::Config;
require Whostmgr::ACLS;
require Cpanel::Rlimit;
require Cpanel::Template;
require Cpanel::Version::Tiny;
###############################################################################

# start main

Whostmgr::ACLS::init_acls();
Cpanel::Rlimit::set_rlimit_to_infinity();

print_header();
is_cache_enabled();
list_enabled();
list_accts();
#enable_cache();

# end main

#################################################
#
#################################################
sub print_header {
    print "Content-Type: text/html\r\n\r\n";
    Whostmgr::HTMLInterface::defheader( lh()->maketext("Managed Hosting Cache") );

    print '<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">';
    print '<link rel="stylesheet" href="https://code.getmdl.io/1.3.0/material.indigo-pink.min.css">';
    print '<script defer src="https://code.getmdl.io/1.3.0/material.min.js"></script>';
}

#################################################
#
#################################################
sub list_enabled {
    print "<br>Cache enabled sites<br>";

    check_enabledsites();
    print "<br>";

    Whostmgr::HTMLInterface::deffooter();
}	

##################################################
#
##################################################
sub list_accts {
    my $filename = '/etc/userdomains';
    open(my $fh, '<:encoding(UTF-8)', $filename)
    or die "Could not open file '$filename' $!";
    print "Cache functions:<br>";
    print "Enable Clear<br>";
    print '<form action = "cachedomain.cgi" method="POST">';   
    while (my $domain = <$fh>) {
       chomp $domain;
       $domain = substr($domain, 0, index($domain, ":"));
       print "<input type='checkbox' name='ledomain' value='$domain'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" if $domain !~ /\*/;
       print "<input type='checkbox' name='leclear' value='$domain'>&nbsp;&nbsp;&nbsp;&nbsp;" if $domain !~ /\*/;
       print "$domain<br>" if $domain !~ /\*/;
    }
    close $fh;
    print '<br><input type="submit" name="submit1" value="Submit">';
}

##################################################
#
##################################################
sub check_enabledsites {
    my @enabledsites = `find /etc/apache2/conf.d/userdata/std/2/*/*/ -name "mhcache.conf"`;
    foreach (@enabledsites) { 
       my @domainsplit = split /\//, $_;
       my $domain = @domainsplit[8];
       my $loadbefore = get_benchmark($domain);
       my $loadafter = benchmark_site($domain);
       print "$domain | Before cache load time: $loadbefore | After cache load time: $loadafter <br>"  
    }
}

##################################################
#
##################################################
sub is_cache_enabled {
    system( '/usr/local/bin/ea_current_to_profile --output=/root/profile-mh2.txt >> /dev/null' );
    my $filename = '/root/profile-mh2.txt';
    my $foundmodcache;
    my $foundmoddiskcache;

    open(my $fh, '<:encoding(UTF-8)', $filename)
    or die "Could not open file '$filename' $!";
    
    while (<$fh>) {
       if ($_ =~ /"ea-apache24-mod_cache"/) {
          $foundmodcache++;
       } elsif (/"ea-apache24-mod_cache_disk"/) {
          $foundmoddiskcache++;
       }
    }

    if ($foundmodcache && $foundmoddiskcache) {
       print "Cache is supported.<br>"
    } elsif ($foundmodcache && !$foundmoddiskcache) {
       print "need to enabled mod diskcache.";
    } elsif ($foundmoddiskcache && !$foundmodcache) {
       print "need to enable mod cache.";
    }
    
}

##################################################
#
##################################################
sub enable_cache {
    # Check if mod_Cache enabled already
    system( '/usr/local/bin/ea_current_to_profile --output=/root/profile-mh-cache.txt >> /dev/null' );

    system( 'sed -i \'/"ea-apache24-mod_bwlimited",/a"ea-apache24-mod_cache",\n"ea-apache24-mod_cache_disk",\' /root/profile-mh-cache.txt' );    
    #system( 'ea_install_profile /root/profile-mh-cache.txt' );
}

##################################################
#
##################################################
sub benchmark_site {
    # get passed arguements
    my ($domain) = @_;

    my $average = `for((i=0; i<3; i++)); do (time -p curl -A "test" "http://\$domain") 2>&1 > /dev/null; done | grep real | awk '{print \$2}' | awk '{avg += (\$1 - avg) / NR;} END {print avg;}'`;

    return $average;
}

##################################################
#
##################################################
sub get_benchmark {
    my ($domain) = @_;

    my $file = '/usr/local/cpanel/whostmgr/docroot/cgi/managedhostcache/benchmarks.ini';
    my $average = benchmark_site($domain);

    open( my $fh, '<', $file)
    or die "Could not open file '$file' $!";
 
    my $count;
    while (<$fh>) {
       if (/^$domain/) {
          $count++;
          my $row = <$fh>;
          chomp $row;
          my @inisplit = split /,/, $_;
          $average= @inisplit[1];
          return $average;
       }
    }
    close $fh;

    if(! $count) {
          open(my $fh, '>>', '/usr/local/cpanel/whostmgr/docroot/cgi/managedhostcache/benchmarks.ini');
          print $fh "$domain,$average";
          close $fh;
    }

    return $average;
}

1;
