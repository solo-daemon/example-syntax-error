import { ethers } from 'hardhat';
import fs from 'fs/promises';

async function main() {
  const [deployer] = await ethers.getSigners();

  console.log('Deploying contracts with the account:', deployer.address);

  // Deploy DAO Token
  const DAOToken = await ethers.getContractFactory('DAOToken');
  const daoToken = await DAOToken.deploy('ZKReview Token', 'ZKR');
  await daoToken.deployed();
  console.log('DAOToken deployed to:', daoToken.address);

  // Deploy DAO
  const ZKReviewDAO = await ethers.getContractFactory('ZKReviewDAO');
  const zkReviewDAO = await ZKReviewDAO.deploy(daoToken.address);
  await zkReviewDAO.deployed();
  console.log('ZKReviewDAO deployed to:', zkReviewDAO.address);

  // Deploy ZKCodeReview
  const ZKCodeReview = await ethers.getContractFactory('ZKCodeReview');
  const zkCodeReview = await ZKCodeReview.deploy(zkReviewDAO.address);
  await zkCodeReview.deployed();
  console.log('ZKCodeReview deployed to:', zkCodeReview.address);

  // Set ZKCodeReview address in DAO
  await zkReviewDAO.setZKReviewContract(zkCodeReview.address);
  console.log('ZKCodeReview address set in DAO');

  // Deploy a sample circuit verifier
  const Verifier = await ethers.getContractFactory('Verifier');
  const verifier = await Verifier.deploy();
  await verifier.deployed();
  console.log('Sample Verifier deployed to:', verifier.address);

  // Register the sample circuit
  const circuitName = 'SampleCircuit';
  const circuitDescription = 'A sample circuit for testing';
  const circuitIPFSCID = 'QmSampleCID';
  await zkCodeReview.registerCircuit(circuitName, circuitDescription, circuitIPFSCID, verifier.address);
  console.log('Sample circuit registered');

  // Save deployment addresses
  const deploymentInfo = {
    DAOToken: daoToken.address,
    ZKReviewDAO: zkReviewDAO.address,
    ZKCodeReview: zkCodeReview.address,
    SampleVerifier: verifier.address,
  };

  await fs.writeFile('deployment-info.json', JSON.stringify(deploymentInfo, null, 2));
  console.log('Deployment info saved to deployment-info.json');
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error