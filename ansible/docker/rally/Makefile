image_name=huikang/ovn-scale-test-rally-upstream

image:
	tar cvzf /tmp/ovn-scale-test.tgz ../../../../ovn-scale-test-github
	tar xvzf /tmp/ovn-scale-test.tgz
	${OVNSUDO} docker build --force-rm=true --no-cache -t ${image_name} .
#	rm -rf ./ovn-scale-test
