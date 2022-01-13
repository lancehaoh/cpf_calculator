import datetime

class State :
    def __init__(self, config):
        self.config_options = config
        self.initial_year = datetime.date.today().year
        self.year = datetime.date.today().year
        self.month = datetime.date.today().month
        self.age = config["current-age"]
        self.oa_balance = config['cpf']['oa']['balance']
        self.sa_balance = config['cpf']['sa']['balance']
        self.ma_balance = config['cpf']['ma']['balance']
        self.frs = config['cpf']['frs']
        self.ma_limit = config['cpf']['ma']['max-allowable-balance']
        self._set_contribution_rates()
        self._set_salary()
        self._reset_last_year_interest()

    def advance(self):
        self._update_age()
        self._update_balances()
        self.notify_when_sa_reached_frs()

    def _update_balances(self):
        self._set_contribution_rates()
        self._set_salary()

        oa_last_year_interest = self.oa_last_year_interest
        sa_last_year_interest = self.sa_last_year_interest
        ma_last_year_interest = self.ma_last_year_interest

        if self.month == 1:
            if self.year != self.initial_year:
                self._set_prevailing_frs()
                self._set_prevailing_ma_limit()
        elif self.month == 12:
            self.oa_balance += oa_last_year_interest
            self.sa_balance += sa_last_year_interest
            self.ma_balance += ma_last_year_interest
            self._overflow_ma()
            self._reset_last_year_interest()

        self.oa_last_year_interest += self._get_oa_monthly_interest()
        self.sa_last_year_interest += self._get_sa_monthly_interest()
        self.ma_last_year_interest += self._get_ma_monthly_interest()

        self.sa_balance += self._get_sa_contribution()

        if self.sa_balance >= self.frs:
            self.oa_balance += self._get_oa_contribution()
        else:
            if self.config_options['cpf']['transfer-from-oa-to-sa-monthly']:
                oa_sa_transfer_bound = min(max(0, self.frs - self.sa_balance), self._get_oa_contribution())
            else:
                oa_sa_transfer_bound = 0
            self.sa_balance += oa_sa_transfer_bound
            self.oa_balance += self._get_oa_contribution() - oa_sa_transfer_bound
            if self.sa_balance < self.frs:
                self.sa_balance += min(max(0, self.frs - self.sa_balance), self.config_options['cpf']['monthly-cash-top-up-to-sa'])

        self.ma_balance += self._get_ma_contribution()
        self._overflow_ma()

    def notify_when_sa_reached_frs(self):
        if self.sa_balance >= self.frs:
            print('SA balance has reached the full retirement sum!!!')

    def _reset_last_year_interest(self):
        self.oa_last_year_interest = 0
        self.sa_last_year_interest = 0
        self.ma_last_year_interest = 0

    def _overflow_ma(self):
        ma_excess = max(0, self.ma_balance - self.ma_limit)
        ma_to_sa = min(ma_excess, max(0, self.frs - self.sa_balance))
        ma_to_oa = ma_excess - ma_to_sa

        self.oa_balance += ma_to_oa
        self.sa_balance += ma_to_sa
        self.ma_balance -= ma_excess

    def _get_oa_monthly_interest(self):
        eligible_for_extra_interest = min(self.oa_balance, self.config_options['cpf']['oa']['extra-interest-cap'])
        extra_interest = eligible_for_extra_interest * (self.config_options['cpf']['extra-interest-rate'] / (12 * 100))
        normal_interest = self.oa_balance * (self.config_options['cpf']['oa']['interest-rate'] / (12 * 100))
        return extra_interest + normal_interest

    def _get_sa_monthly_interest(self):
        oa_eligible_extra = min(self.oa_balance, self.config_options['cpf']['oa']['extra-interest-cap'])
        eligible_for_extra_interest = min(self.config_options['cpf']['total-extra-interest-cap'] - oa_eligible_extra, self.sa_balance)
        extra_interest = eligible_for_extra_interest * (self.config_options['cpf']["extra-interest-rate"] / (12 * 100))
        normal_interest = self.sa_balance * (self.config_options['cpf']['sa']["interest-rate"] / (12 * 100))
        return extra_interest + normal_interest

    def _get_ma_monthly_interest(self):
        oa_eligible_extra = min(self.oa_balance, self.config_options['cpf']['oa']["extra-interest-cap"])
        sa_eligible_extra = min(self.config_options['cpf']["total-extra-interest-cap"] - oa_eligible_extra, self.sa_balance)
        eligible_for_extra_interest = min(self.config_options['cpf']['total-extra-interest-cap'] - oa_eligible_extra - sa_eligible_extra, self.ma_balance)
        extra_interest = eligible_for_extra_interest * (self.config_options['cpf']['extra-interest-rate'] / (12 * 100))
        normal_interest = self.ma_balance * (self.config_options['cpf']['ma']['interest-rate'] / (12 * 100))
        return extra_interest + normal_interest

    def _update_age(self):
        self.year += 1 if self.month == 12 else 0
        self.month = (self.month % 12) + 1
        self.age += 1 if self.month == self.config_options['birth-month'] else 0

    def _set_contribution_rates(self):
        for x in self.config_options['cpf']['contribution-rate']:
            if self.age in range(x['lower-limit'], x['upper-limit'] + 1):
                self.oa_rate, self.sa_rate, self.ma_rate = x['oa'], x['sa'], x['ma']
                break
        else:
            raise Exception('Could not find contribution rates for age {}'.format(self.age))

    def _set_salary(self):
        for x in self.config_options['salary']:
            if self.age in range(x['lower-limit'], x['upper-limit'] + 1):
                self.salary = x['salary']
                break
        else:
            raise Exception('Could not find salary info for age {}'.format(self.salary))

    def _set_prevailing_frs(self):
        self.frs += self.frs * (self.config_options['cpf']['frs-inflation-rate'] / 100)

    def _set_prevailing_ma_limit(self):
        self.ma_limit += self.ma_limit * (self.config_options['cpf']['ma']['max-allowable-balance-inflation-rate'] / 100)

    def _get_oa_contribution(self):
        return min(self.config_options['cpf']['salary-limit'], self.salary) * (self.oa_rate / 100)

    def _get_sa_contribution(self):
        return min(self.config_options['cpf']['salary-limit'], self.salary) * (self.sa_rate / 100)

    def _get_ma_contribution(self):
        return min(self.config_options['cpf']['salary-limit'], self.salary) * (self.ma_rate / 100)

    def __str__(self):
        return dict([
            ("year", self.year),
            ("month", self.month),
            ("age", self.age),
            ("oa_balance", self.oa_balance),
            ("sa_balance", self.sa_balance),
            ("frs", self.frs)
        ]).__str__()
