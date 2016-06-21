image_name=huikang/ovn-scale-test-ovn-local-master-profiling

ifndef ovsrepo
ovs_repo=https://github.com/huikang/ovs.git
endif
ifndef ovsbranch
ovs_branch=profiling-debug
endif

image:
	echo "ovs_repo: ${ovs_repo} ovs_branch: ${ovs_branch}"
	${OVNSUDO} docker build --build-arg ovsrepo=${ovs_repo} --build-arg ovsbranch=${ovs_branch} --force-rm=true --no-cache=true -t ${image_name} .
