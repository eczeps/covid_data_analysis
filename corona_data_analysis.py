import matplotlib.pyplot as plt
from scipy.stats import kde, pearsonr
import csv
import numpy as np

###
#run this file to generate all graphs and do all the statistical analysis. 
#In the main method, you can comment out either the block for everything using a certain dataset,
#or comment out individual lines creating graphs or doing statistical analysis.
#
#Your file structure should have this file, 103 csv files (50 population; 50 income; 2 usafacts; 1 nytimes),
#and a folder called results all in one place. I may tidy this up later but it's working for now
#
#To use this, just download all the CSV files and then change the date in main() for the new york times CSV before running it
#CSV Files to download:
#A file for each individual state, named income_#.csv where # is from 0 to 49 (https://data.ers.usda.gov/reports.aspx?ID=17828)
#A file for each individual state, named population_#.csv where # is from 0 to 49 (https://data.ers.usda.gov/reports.aspx?ID=17827)
#The two files at the end of this article: https://usafacts.org/visualizations/coronavirus-covid-19-spread-map/
#This file: https://github.com/nytimes/covid-19-data/blob/master/us-counties.csv
###




#download https://data.ers.usda.gov/reports.aspx?ID=17828 for each state & digest the files
def read_median_income_data():
    result = {}
    for num in range(50):
        #for each state; this requires files are saved in format income_0.csv, income_1.csv, etc in alphabetical order by state
        filename = "income_" + str(num) + ".csv"
        with open(filename, 'r') as csv_file:
            data_iter = csv.reader(csv_file, delimiter = ',', quotechar = '"')
            data = [data for data in data_iter][3:]
            for county_list in data:
                #get all data for a county as a value under the FIPS key
                result[county_list[0]] = county_list[1:]
    #make an entry that combines all of NYC with fips = 1
    #using data from https://www.statista.com/statistics/205974/median-household-income-in-new-york/
    result[1] = '$67,274'
    return result


#from https://data.ers.usda.gov/reports.aspx?ID=17827
def read_population_data():
    result = {}
    for num in range(50):
        #for each state; this requires files are saved in format income_0.csv, income_1.csv, etc in alphabetical order by state
        filename = "population_" + str(num) + ".csv"
        with open(filename, 'r') as csv_file:
            data_iter = csv.reader(csv_file, delimiter = ',', quotechar = '"')
            data = [data for data in data_iter][2:-2]
            for county_list in data:
                #get 2018 population as a value under the key (FIPS code)
                result[county_list[0]] = county_list[-3]
    #make an entry that combines all of NYC with fips = 1
    #using data from  https://www1.nyc.gov/site/planning/planning-level/nyc-population/current-future-populations.page
    result[1] = 8,398,748
    return result


#https://usafacts.org/visualizations/coronavirus-covid-19-spread-map/
def read_usafacts_data(filename):
    result = {}
    with open(filename, 'r') as csv_file:
        data_iter = csv.reader(csv_file, delimiter = ',', quotechar = '"')
        data = [data for data in data_iter][1:]
        print('num counties in usafacts data: ' + str(len(data)))
        for county_list in data:
            #get all data for a county as a value under the FIPS key
            fips = county_list[0]
            if int(fips) < 9999:
                #add a 0 onto the beginning of fips that aren't 5 digits by themselves
                fips = str(0) + str(fips)
            #add a column that's the sum of all the days so far:
            sum = 0
            for num in range(4, len(county_list)):
                try:
                    sum += int(county_list[num])
                except ValueError:
                    sum += 0
            result[fips] = sum
    return result


#from https://github.com/nytimes/covid-19-data/blob/master/us-counties.csv
def read_nytimes_county_data(most_recent_date):
    #most_recent_date is the most recent date the file has data for, i.e. 2020-03-25
    deaths_result = {}
    cases_result = {}
    with open('us-counties.csv', 'r') as csv_file:
        data_iter = csv.reader(csv_file, delimiter = ',', quotechar = '"')
        data = [data for data in data_iter if data[0] == most_recent_date][1:]
        print('num counties in nytimes data: ' + str(len(data)))
        for county_list in data:
            #get all data for a county as a value under the FIPS key
            fips = county_list[3]
            #handle new york city specially; make up a FIPS code of 1 to use for data analysis:
            if fips is '' and county_list[1] is "New York City":
                deaths_result[1] = int(county_list[-1])
                cases_result[1] = int(county_list[-2])
            deaths_result[fips] = int(county_list[-1])
            cases_result[fips] = int(county_list[-2])
    return cases_result, deaths_result


def combine_income_deaths_cases_population(cases_data, deaths_data, income_lists, population_data):
    result = {}
    keys = income_lists.keys()
    num_excluded_counties = 0
    for key in keys:
        try:
            death_data = deaths_data[key]
            income_data = income_lists[key]
            case_data = cases_data[key]
            population = population_data[key].replace(',','')
            county_data = income_data[0]
            #if death_data is not 0 or case_data is not 0:
            try:
                cleaned_income = int(income_data[10][1:].replace(',',''))
                result[key] = {'deaths':death_data, 'cases':case_data, 'income':cleaned_income, 'population':population, 'county_data': county_data}
            except ValueError:
                #print('invalid literal for int() with base 10: ' + str(income_data[10][1:].replace(',','')))
                #this seems to only be happening once in the new york times dataset so...
                num_excluded_counties += 1
        except KeyError:
            num_excluded_counties += 1
    print('number of all US counties excluded from dataset due to missing data: ' + str(num_excluded_counties))
    return result




def sort_data_by_income(combined_income_deaths):
    zipped_list = []
    for key in combined_income_deaths.keys():
        income = combined_income_deaths[key]['income']
        deaths = combined_income_deaths[key]['deaths']
        cases = combined_income_deaths[key]['cases']
        population = combined_income_deaths[key]['population']
        zipped_list.append((income, cases, deaths, population))
    sorted_list = sorted(zipped_list, key=lambda x: x[0])
    sorted_incomes = [elt[0] for elt in sorted_list]
    sorted_cases = [elt[1] for elt in sorted_list]
    sorted_deaths = [elt[2] for elt in sorted_list]
    sorted_population = [elt[3] for elt in sorted_list]
    return (sorted_incomes, sorted_cases, sorted_deaths, sorted_population)


def show_both_vs_income(sorted_data_tuple, source):
    sorted_incomes, sorted_cases, sorted_deaths, sorted_populations = sorted_data_tuple
    axes = plt.gca()
    plt.scatter(sorted_incomes, sorted_cases, color='blue')
    plt.scatter(sorted_incomes, sorted_deaths, color='red')
    plt.xlabel('Median County Income')
    plt.ylabel('Cumulative County Cases & Deaths Due to COVID-19')
    axes.set_yscale('log', basey=2)
    axes.axis([min(sorted_incomes), max(sorted_incomes), 1, max(sorted_cases)])
    axes.legend(['Cumulative confirmed cases', 'Cumulative confirmed deaths'])
    plt.tight_layout()
    plt.savefig('results/' + source + '_deaths_and_cases.png')
    plt.close()



def show_deaths_vs_income(sorted_data_tuple, source):
    sorted_incomes, sorted_cases, sorted_deaths, sorted_populations = sorted_data_tuple
    axes = plt.gca()
    plt.scatter(sorted_incomes, sorted_deaths, color='red')
    plt.xlabel('Median County Income')
    plt.ylabel('Cumulative County Deaths Due to COVID-19')
    axes.set_yscale('log', basey=2)
    axes.axis([min(sorted_incomes), max(sorted_incomes), 1, max(sorted_deaths)])
    axes.legend(['Cumulative confirmed deaths'])
    plt.tight_layout()
    plt.savefig('results/' + source + '_deaths.png')
    plt.close()


def show_deaths_vs_income_density(sorted_data_tuple, source):
    sorted_incomes, sorted_cases, sorted_deaths, sorted_populations = sorted_data_tuple
    axes = plt.gca()
    nbins=300
    k = kde.gaussian_kde([sorted_incomes,sorted_deaths])
    xi, yi = np.mgrid[min(sorted_incomes):max(sorted_incomes):nbins*1j, min(sorted_deaths):max(sorted_deaths):nbins*1j]
    zi = k(np.vstack([xi.flatten(), yi.flatten()]))
    plt.pcolormesh(xi, yi, zi.reshape(xi.shape))
    plt.xlabel('Median County Income')
    plt.ylabel('i am confused. but its cumulative deaths')
    axes.set_ylim([0,50])
    plt.tight_layout()
    plt.savefig('results/' + source + '_deaths_density.png')
    plt.close()


def show_cases_vs_income(sorted_data_tuple, source):
    sorted_incomes, sorted_cases, sorted_deaths, sorted_populations = sorted_data_tuple
    axes = plt.gca()
    plt.scatter(sorted_incomes, sorted_cases, color='blue')
    plt.xlabel('Median County Income')
    plt.ylabel('Cumulative County Cases Due to COVID-19')
    axes.set_yscale('log', basey=2)
    axes.axis([min(sorted_incomes), max(sorted_incomes), 1, max(sorted_cases)])
    axes.legend(['Cumulative confirmed cases'])
    plt.tight_layout()
    plt.savefig('results/' + source + '_cases.png')
    plt.close()


def show_cases_vs_income_density(sorted_data_tuple, source):
    sorted_incomes, sorted_cases, sorted_deaths, sorted_populations = sorted_data_tuple
    axes = plt.gca()
    nbins=300
    k = kde.gaussian_kde([sorted_incomes,sorted_cases])
    xi, yi = np.mgrid[min(sorted_incomes):max(sorted_incomes):nbins*1j, min(sorted_cases):max(sorted_cases):nbins*1j]
    zi = k(np.vstack([xi.flatten(), yi.flatten()]))
    plt.pcolormesh(xi, yi, zi.reshape(xi.shape))
    plt.xlabel('Median County Income')
    plt.ylabel('i am confused. but its cumulative cases')
    axes.set_ylim([0,2000])
    plt.tight_layout()
    plt.savefig('results/' + source + '_cases_density.png')
    plt.close()



def show_deaths_vs_income_per_capita(sorted_data_tuple, source):
    sorted_incomes, sorted_cases, sorted_deaths, sorted_populations = sorted_data_tuple
    sorted_deaths_per_capita = [(float(sorted_deaths[i])/float(sorted_populations[i])) for i in range(len(sorted_populations))]
    axes = plt.gca()
    plt.scatter(sorted_incomes, sorted_deaths_per_capita, color='red')
    plt.xlabel('Median County Income')
    plt.ylabel('County Deaths Per Capita Due to COVID-19')
    plt.yscale("log")
    axes.axis([min(sorted_incomes), max(sorted_incomes), .0000001, max(sorted_deaths_per_capita)])
    axes.legend(['Confirmed deaths per capita'])
    plt.tight_layout()
    plt.savefig('results/' + source + '_deaths_per_capita.png')
    plt.close()


def show_deaths_vs_income_density_per_capita(sorted_data_tuple, source):
    sorted_incomes, sorted_cases, sorted_deaths, sorted_populations = sorted_data_tuple
    sorted_deaths_per_capita = [(float(sorted_deaths[i])/float(sorted_populations[i])) for i in range(len(sorted_populations))]
    axes = plt.gca()
    nbins=300
    k = kde.gaussian_kde([sorted_incomes,sorted_deaths_per_capita])
    xi, yi = np.mgrid[min(sorted_incomes):max(sorted_incomes):nbins*1j, min(sorted_deaths_per_capita):max(sorted_deaths_per_capita):nbins*1j]
    zi = k(np.vstack([xi.flatten(), yi.flatten()]))
    plt.pcolormesh(xi, yi, zi.reshape(xi.shape))
    plt.xlabel('Median County Income')
    plt.ylabel('i am confused. but its per capita deaths')
    axes.set_ylim([0,.00005])
    plt.tight_layout()
    plt.savefig('results/' + source + '_deaths_density_per_capita.png')
    plt.close()


def show_cases_vs_income_per_capita(sorted_data_tuple, source):
    sorted_incomes, sorted_cases, sorted_deaths, sorted_populations = sorted_data_tuple
    sorted_cases_per_capita = [(float(sorted_cases[i])/float(sorted_populations[i])) for i in range(len(sorted_populations))]
    axes = plt.gca()
    plt.scatter(sorted_incomes, sorted_cases_per_capita, color='blue')
    plt.xlabel('Median County Income')
    plt.ylabel('County Cases Per Capita Due to COVID-19')
    plt.yscale("log")
    #this excludes all places with 0 cases
    axes.axis([min(sorted_incomes), max(sorted_incomes), .000001, max(sorted_cases_per_capita)])
    axes.legend(['Confirmed cases per capita'])
    plt.tight_layout()
    plt.savefig('results/' + source + '_cases_per_capita.png')
    plt.close()


def show_cases_vs_income_density_per_capita(sorted_data_tuple, source):
    sorted_incomes, sorted_cases, sorted_deaths, sorted_populations = sorted_data_tuple
    sorted_cases_per_capita = [(float(sorted_cases[i])/float(sorted_populations[i])) for i in range(len(sorted_populations))]
    axes = plt.gca()
    nbins=300
    k = kde.gaussian_kde([sorted_incomes,sorted_cases_per_capita])
    xi, yi = np.mgrid[min(sorted_incomes):max(sorted_incomes):nbins*1j, min(sorted_cases_per_capita):max(sorted_cases_per_capita):nbins*1j]
    zi = k(np.vstack([xi.flatten(), yi.flatten()]))
    plt.pcolormesh(xi, yi, zi.reshape(xi.shape))
    plt.xlabel('Median County Income')
    plt.ylabel('i am confused. but its per capita cases')
    axes.set_ylim([0,.002])
    plt.tight_layout()
    plt.savefig('results/' + source + '_cases_density_per_capita.png')
    plt.close()


def show_deaths_per_cases(sorted_data_tuple, source):
    sorted_incomes, sorted_cases, sorted_deaths, sorted_populations = sorted_data_tuple
    sorted_deaths_per_cases = [(float(sorted_deaths[i])/float(sorted_cases[i])) if sorted_cases[i] is not 0 else 0 for i in range(len(sorted_cases))]
    axes = plt.gca()
    plt.scatter(sorted_incomes, sorted_deaths_per_cases, color='green')
    plt.xlabel('Median County Income')
    plt.ylabel('Ratio of County Deaths to Cases of COVID-19')
    plt.yscale("log")
    #this excludes all places with 0 cases
    axes.axis([min(sorted_incomes), max(sorted_incomes), .0001, max(sorted_deaths_per_cases)])
    axes.legend(['Ratio of deaths to cases'])
    plt.tight_layout()
    plt.savefig('results/' + source + '_deaths_per_cases.png')
    plt.close()


def do_stats(sorted_data_tuple, source):
    sorted_incomes, sorted_cases, sorted_deaths, sorted_populations = sorted_data_tuple
    sorted_deaths_per_capita = [(float(sorted_deaths[i])/float(sorted_populations[i])) for i in range(len(sorted_populations))]
    sorted_cases_per_capita = [(float(sorted_cases[i])/float(sorted_populations[i])) for i in range(len(sorted_populations))]
    sorted_deaths_per_cases = [(float(sorted_deaths[i])/int(sorted_cases[i])) if int(sorted_cases[i]) is not 0 else 0 for i in range(len(sorted_cases))]
    np_sorted_incomes = np.array(sorted_incomes)
    np_sorted_cases = np.array(sorted_cases)
    np_sorted_deaths = np.array(sorted_deaths)
    np_sorted_cases_per_capita = np.array(sorted_cases_per_capita)
    np_sorted_deaths_per_capita = np.array(sorted_deaths_per_capita)
    np_sorted_deaths_per_cases = np.array(sorted_deaths_per_cases)
    r_p_income_cases = pearsonr(np_sorted_incomes, np_sorted_cases)
    r_p_income_deaths = pearsonr(np_sorted_incomes, np_sorted_deaths)
    r_p_income_cases_per_capita = pearsonr(np_sorted_incomes, np_sorted_cases_per_capita)
    r_p_income_deaths_per_capita = pearsonr(np_sorted_incomes, np_sorted_deaths_per_capita)
    r_p_deaths_per_cases = pearsonr(np_sorted_incomes, np_sorted_deaths_per_cases)
    print('r and p value for income vs cases from ' + source + ' data: r=' + str(r_p_income_cases[0].round(3)) + '\n p=' + str(r_p_income_cases[1]))
    print('r and p value for income vs deaths from ' + source + ' data: r=' + str(r_p_income_deaths[0].round(3)) + '\n p=' + str(r_p_income_deaths[1]))
    print('r and p value for income vs cases per capita from ' + source + ' data: r=' + str(r_p_income_cases_per_capita[0].round(3)) + '\n p=' + str(r_p_income_cases_per_capita[1]))
    print('r and p value for income vs deaths per capita from ' + source + ' data: r=' + str(r_p_income_deaths_per_capita[0].round(3)) + '\n p=' + str(r_p_income_deaths_per_capita[1]))
    print('r and p value for income vs deaths per cases from ' + source + ' data: r=' + str(r_p_deaths_per_cases[0].round(3)) + '\n p=' + str(r_p_deaths_per_cases[1]))


def other_fun_dataset_facts(sorted_data_tuple, source):
    sorted_incomes, sorted_cases, sorted_deaths, sorted_populations = sorted_data_tuple
    print('size of income dataset from ' + source + ': ' + str(len(sorted_incomes)) + ' counties')
    print('size of cases dataset from ' + source + ': ' + str(len(sorted_cases)) + ' counties')
    print('size of deaths dataset from ' + source + ': ' + str(len(sorted_deaths)) + ' counties')
    print('size of population dataset from ' + source + ': ' + str(len(sorted_populations)) + ' counties')



def main():

    #ingesting all the csv files:
    income_lists = read_median_income_data()
    population_data = read_population_data()

    
    usafacts_deaths_data = read_usafacts_data('covid_deaths_usafacts.csv')
    usafacts_cases_data = read_usafacts_data('covid_confirmed_usafacts.csv')

    #Remember to update this date with the most current date in the nytimes file!
    nytimes_cases_data, nytimes_deaths_data = read_nytimes_county_data('2020-03-27')


    #use this block for usafacts data
    usafacts_combined_income_deaths = combine_income_deaths_cases_population(usafacts_cases_data, usafacts_deaths_data, income_lists, population_data)
    usafacts_sorted_data_tuple = sort_data_by_income(usafacts_combined_income_deaths)
    do_stats(usafacts_sorted_data_tuple, 'usafacts')
    other_fun_dataset_facts(usafacts_sorted_data_tuple, 'usafacts')
    show_deaths_vs_income(usafacts_sorted_data_tuple, 'usafacts')
    show_cases_vs_income(usafacts_sorted_data_tuple, 'usafacts')
    show_deaths_vs_income_per_capita(usafacts_sorted_data_tuple, 'usafacts')
    show_cases_vs_income_per_capita(usafacts_sorted_data_tuple, 'usafacts')
    #show_deaths_vs_income_density(usafacts_sorted_data_tuple, 'usafacts')
    #show_deaths_vs_income_density_per_capita(usafacts_sorted_data_tuple, 'usafacts')
    show_deaths_per_cases(usafacts_sorted_data_tuple, 'usafacts')


    #use this block for nytimes data
    nytimes_combined_income_deaths = combine_income_deaths_cases_population(nytimes_cases_data, nytimes_deaths_data, income_lists, population_data)
    nytimes_sorted_data_tuple = sort_data_by_income(nytimes_combined_income_deaths)
    do_stats(nytimes_sorted_data_tuple, 'nytimes')
    other_fun_dataset_facts(nytimes_sorted_data_tuple, 'nytimes')
    show_deaths_vs_income(nytimes_sorted_data_tuple, 'nytimes')
    show_cases_vs_income(nytimes_sorted_data_tuple, 'nytimes')
    show_deaths_vs_income_per_capita(nytimes_sorted_data_tuple, 'nytimes')
    show_cases_vs_income_per_capita(nytimes_sorted_data_tuple, 'nytimes')
    #show_deaths_vs_income_density(nytimes_sorted_data_tuple, 'nytimes')
    #show_deaths_vs_income_density_per_capita(nytimes_sorted_data_tuple, 'nytimes')
    show_deaths_per_cases(nytimes_sorted_data_tuple, 'nytimes')


main()
