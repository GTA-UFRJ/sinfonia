**Sinfonia**
============
Official repository for Sinfonia, a Network Function Virtualization orchestration tool mantained by GTA/UFRJ.



Installation
------------

The Sinfonia orchestration tool is built on top of the Open Platform for Network Function Virtualization (OPNFV) and the Django Python framework.  We need to install both modules to make the tool operational.

Installing OPNFV
----------------
OPNFV is a cloud operating system platform mantained by the Linux Foundation that provides the tools for the NFV orchestration Sinfonia is based upon. To install it, please read the [official documentation](http://docs.opnfv.org/en/stable-danube/release/installation.introduction.html) for its current relase. We recommend the [deployment through Fuel](http://docs.opnfv.org/en/stable-danube/submodules/fuel/docs/release/installation/index.html#fuel-installation) as it is easier to debug and it has a graphical installation tool. The hardware requirements for a minimum OPNFV environment deployment through Fuel are:

 - 1 Fuel Master node
 	- **CPU:**	Dual-core
	- **RAM:**	2GB 
	- **Disk:** 	50GB per node
	- **NIC:**  1 Gigabit network port
 - 1 Controller node
	- **CPU:**	1 socket x86_AMD64 with Virtualization support
	- **RAM:**	16GB per server (Depending on VNF work load)
	- **Disk:**	256GB 10kRPM spinning disks
 - 1 Compute node
	- **CPU:**	1 socket x86_AMD64 with Virtualization support
	- **RAM:**	16GB/server (Depending on VNF work load)
	- **Disk:**	256GB 10kRPM spinning disks
 - Networks
	- 4 Tagged VLANs (PUBLIC, MGMT, STORAGE, PRIVATE)
	- 1 Un-Tagged VLAN for PXE Boot - ADMIN Network
*Note: These can be allocated to a single NIC - or spread out over multiple NICs as your hardware supports.*
 
 Sinfonia was originally developed in a 4-node deployment (1 controller node, 3 compute nodes) of the Danube 3.0 release of OPNFV and it should be compatible with previous and future releases.  


Installing Sinfonia
----------------
Sinfonia itself is written in Python and uses the Django framework to build its interface and main server. To install the tool simply clone the git repository:

     git clone https://github.com/gfrebello/sinfonia.git

And install its dependencies with `pip`:
		
    cd ./sinfonia
    pip install -r requirements.txt

If you are running Python < 2.7.9 and don't have `pip` installed, check its [installation guide](https://pip.pypa.io/en/stable/installing/). By running  these simple commands, you should have a full installation of Sinfonia. 

Configuring and running 
----------------

After OPNFV is up and running and the the Sinfonia installation setup is done, we need to configure our orchestrator and initialize our blockchain modules. First, put the orchestrator file inside the node controller and run it in a Python console:

    scp orchestrator.py root@<controller IP>:~/
	ssh root@<controller IP>
	screen python
	>>> from orchestrator import *
	>>> 

Note: Because we are connecting remotely to the controller, the `screen` package is used as a way to keep the orchestrator running if the `ssh` connection is lost. Using simply `python` would have been enough if we had physical access to the controller's terminal.

Then, at your local machine, run the blockchain modules which will store our sensitive commands. 

    screen python
	>>> from backChain.chainNode import *
	>>> main()
Detatch from the screen with Ctrl+A then Ctrl+D and:

    screen python
	>>> from backChain.managementClient import *
	>>> main()

Note: The use of `screen` here is once again a way to simplify our deployment. This is equivalent to running the Python consoles on two bash terminals. 

Finally, start Sinfonia's main server with:

    python manage.py runserver

And check http://localhost/dashboard. You should see an authentication screen. Register yourself and enjoy Sinfonia!
