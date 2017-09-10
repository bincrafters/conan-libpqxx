
#include <iostream>
#include <pqxx/pqxx>

int main()
{
    std::cout << "Environment:" << std::endl;
    std::cout << " - PGDATABASE=" << std::getenv("PGDATABASE") << std::endl;
    std::cout << " - PGUSER=" << std::getenv("PGUSER") << std::endl;
    try
    {
        pqxx::connection C;
        std::cout << "Connected to " << C.dbname() << std::endl;
        pqxx::work W(C);

        // Create table and populate
        W.exec("CREATE TABLE IF NOT EXISTS employee (name varchar (50) NOT NULL, salary decimal NOT NULL);");
        W.exec("INSERT INTO employee (name, salary) values ('jgsogo', 1000);");

        // Read and double
        pqxx::result R = W.exec("SELECT name FROM employee");

        std::cout << "Found " << R.size() << " employees:" << std::endl;
        for (auto row: R)
            std::cout << row[0].c_str() << std::endl;

        std::cout << "Doubling all employees' salaries..." << std::endl;
        W.exec("UPDATE employee SET salary = salary*2");

        std::cout << "Making changes definite: ";
        W.commit();
        std::cout << "OK." << std::endl;
    }
    catch (const std::exception &e)
    {
        std::cerr << e.what() << std::endl;
        return 1;
    }
    return 0;
}
