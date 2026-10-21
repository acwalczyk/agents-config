.PHONY: check doctor test update
check:
	./scripts/setup.sh --check
doctor:
	./scripts/doctor.sh
test:
	python3 -m unittest discover -s tests/deployment -v
	@for script in scripts/*.sh; do sh -n "$$script" || exit; done
	git diff --check
	git diff --cached --check
update:
	./scripts/update.sh
